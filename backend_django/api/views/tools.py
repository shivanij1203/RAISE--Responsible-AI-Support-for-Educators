from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from api.models import AITool, UserProfile, Project
from api.serializers import AIToolSerializer


def serialize_ai_tool(tool: AITool, include_guidance: bool = False) -> dict:
    """Serialize an AITool instance to a camelCase dict for the frontend."""
    return AIToolSerializer(tool, context={'include_guidance': include_guidance}).data


@api_view(['GET', 'POST'])
def ai_tool_list_create(request: Request) -> Response:
    """List all AI tools, or create a new one (faculty only)."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        tools = AITool.objects.all()
        tool_type = request.query_params.get('tool_type')
        category = request.query_params.get('category')
        tool_status = request.query_params.get('status')
        search = request.query_params.get('search', '').strip()
        if tool_type:
            tools = tools.filter(tool_type=tool_type)
        if category:
            tools = tools.filter(category=category)
        if tool_status:
            tools = tools.filter(status=tool_status)
        if search:
            tools = tools.filter(name__icontains=search)
        return Response([serialize_ai_tool(t) for t in tools])

    # POST -- faculty only
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'student'})
    if profile.role != 'faculty':
        return Response({"error": "Only faculty can add tools"}, status=status.HTTP_403_FORBIDDEN)

    name = request.data.get('name', '').strip()
    category = request.data.get('category', '')
    if not name or not category:
        return Response({"error": "Name and category are required"}, status=status.HTTP_400_BAD_REQUEST)

    tool = AITool.objects.create(
        tool_type=request.data.get('tool_type', 'ai'),
        name=name,
        description=request.data.get('description', ''),
        vendor=request.data.get('vendor', ''),
        category=category,
        status=request.data.get('status', 'under_review'),
        risk_notes=request.data.get('risk_notes', ''),
        website_url=request.data.get('website_url', ''),
        added_by=request.user,
    )
    return Response(serialize_ai_tool(tool), status=status.HTTP_201_CREATED)


@api_view(['PUT'])
def ai_tool_update(request: Request, tool_id: int) -> Response:
    """Update an existing AI tool (faculty only)."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'student'})
    if profile.role != 'faculty':
        return Response({"error": "Only faculty can update tools"}, status=status.HTTP_403_FORBIDDEN)

    try:
        tool = AITool.objects.get(id=tool_id)
    except AITool.DoesNotExist:
        return Response({"error": "Tool not found"}, status=status.HTTP_404_NOT_FOUND)

    for field in ['name', 'description', 'vendor', 'category', 'status', 'risk_notes', 'tool_type', 'website_url']:
        if field in request.data:
            setattr(tool, field, request.data[field])
    tool.save()

    return Response(serialize_ai_tool(tool))


@api_view(['GET'])
def ai_tool_detail(request: Request, tool_id: int) -> Response:
    """Get tool details with compliance guidance and activity history."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        tool = AITool.objects.get(id=tool_id)
    except AITool.DoesNotExist:
        return Response({"error": "Tool not found"}, status=status.HTTP_404_NOT_FOUND)

    tool_data = serialize_ai_tool(tool, include_guidance=True)

    # Activity history — projects using this tool with their use case and compliance status
    projects_using = tool.projects.select_related('user').prefetch_related('checkpoints').all()
    activity_history = []
    for p in projects_using:
        cps = list(p.checkpoints.all())
        total = len(cps)
        done = sum(1 for c in cps if c.completed)
        pct = round((done / total) * 100) if total > 0 else 0
        activity_history.append({
            'id': str(p.id),
            'name': p.name,
            'owner': p.user.first_name or p.user.email,
            'aiUseCase': p.ai_use_case,
            'compliancePct': pct,
            'checkpointsDone': done,
            'checkpointsTotal': total,
            'createdAt': p.created_at.isoformat(),
        })

    tool_data['activityHistory'] = activity_history

    return Response(tool_data)


@api_view(['GET'])
def tool_insights(request: Request) -> Response:
    """Return institution-wide AI tool usage and compliance stats."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    from collections import Counter
    from django.db.models import Count
    from api.models import Checkpoint

    total_tools = AITool.objects.count()
    total_activities = Project.objects.count()

    tools_with_count = (
        AITool.objects
        .annotate(activity_count=Count('projects'))
        .filter(activity_count__gt=0)
        .order_by('-activity_count')[:5]
    )
    top_tools = [
        {
            'id': t.id,
            'name': t.name,
            'category': t.category,
            'activityCount': t.activity_count,
        }
        for t in tools_with_count
    ]

    use_case_counter = Counter(
        Project.objects.values_list('ai_use_case', flat=True)
    )
    top_use_cases = [
        {'useCase': uc, 'count': c}
        for uc, c in use_case_counter.most_common(5)
        if uc
    ]

    total_checkpoints = Checkpoint.objects.count()
    completed_checkpoints = Checkpoint.objects.filter(completed=True).count()
    pass_rate = (
        round(100 * completed_checkpoints / total_checkpoints, 1)
        if total_checkpoints else 0
    )

    return Response({
        'totalTools': total_tools,
        'totalActivities': total_activities,
        'topTools': top_tools,
        'topUseCases': top_use_cases,
        'overallPassRate': pass_rate,
        'totalCheckpoints': total_checkpoints,
        'completedCheckpoints': completed_checkpoints,
    })

