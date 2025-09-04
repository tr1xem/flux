from ignis import widgets
from ignis.services.hyprland import HyprlandService, HyprlandWorkspace
from ignis.services.niri import NiriService, NiriWorkspace

hyprland = HyprlandService.get_default()
niri = NiriService.get_default()

# PERSISTENT_WORKSPACES = [1, 2, 3, 4, 5]

PERSISTENT_WORKSPACES = []

# CUSTOM_LABELS = {
#     1: "一",
#     2: "二",
#     3: "三",
#     4: "四",
#     5: "五",
#     6: "六",
#     7: "七",
#     8: "八",
#     9: "九",
#     10: "十",
# }

CUSTOM_LABELS = {
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "10",
}


def get_workspace_label(workspace_id: int) -> str:
    return CUSTOM_LABELS.get(workspace_id, str(workspace_id))


class WorkspaceSwitcher:
    @staticmethod
    def switch_to_persistent_workspace(workspace_id: int) -> None:
        if hyprland.is_available:
            hyprland.switch_to_workspace(workspace_id)
        elif niri.is_available:
            niri.switch_to_workspace(workspace_id)


def create_persistent_workspace_button(
    workspace_id: int, is_active: bool = False, has_windows: bool = False
) -> widgets.Button:
    widget = widgets.Button(
        css_classes=["workspace"],
        on_click=lambda x: WorkspaceSwitcher.switch_to_persistent_workspace(
            workspace_id
        ),
        child=widgets.Label(label=get_workspace_label(workspace_id)),
    )

    if is_active:
        widget.add_css_class("active")
    elif has_windows:
        widget.add_css_class("occupied")
    else:
        widget.add_css_class("empty")

    return widget


def hyprland_workspace_button(workspace: HyprlandWorkspace) -> widgets.Button:
    widget = widgets.Button(
        css_classes=["workspace"],
        on_click=lambda x: workspace.switch_to(),
        child=widgets.Label(label=get_workspace_label(workspace.id)),
    )

    if workspace.id == hyprland.active_workspace.id:
        widget.add_css_class("active")

    return widget


def niri_workspace_button(workspace: NiriWorkspace) -> widgets.Button:
    widget = widgets.Button(
        css_classes=["workspace"],
        on_click=lambda x: workspace.switch_to(),
        child=widgets.Label(label=get_workspace_label(workspace.idx)),
    )

    if workspace.is_active:
        widget.add_css_class("active")

    return widget


def workspace_button(workspace) -> widgets.Button:
    if hyprland.is_available:
        return hyprland_workspace_button(workspace)
    elif niri.is_available:
        return niri_workspace_button(workspace)
    else:
        return widgets.Button()


def scroll_workspaces(direction: str) -> None:
    if hyprland.is_available:
        current = hyprland.active_workspace.id
        if direction == "up":
            target = current - 1
            hyprland.switch_to_workspace(target)
        else:
            target = current + 1
            if target == 11:
                return
            hyprland.switch_to_workspace(target)
    elif niri.is_available:
        # Get active workspace for Niri
        active_workspaces = [ws for ws in niri.workspaces if ws.is_active]
        if not active_workspaces:
            return
        
        current = active_workspaces[0].idx
        if direction == "up":
            target = current - 1
            if target > 0:
                niri.switch_to_workspace(target)
        else:
            target = current + 1
            if target <= 10:
                niri.switch_to_workspace(target)


class Workspaces(widgets.Box):
    def __init__(self, monitor_name: int):
        self.monitor_name = monitor_name

        if hyprland.is_available:
            child_content = hyprland.bind_many(
                ["workspaces", "active_workspace"], transform=self._hyprland_transform
            )
        elif niri.is_available:
            child_content = niri.bind("workspaces", transform=self._niri_transform)
        else:
            child_content = []

        super().__init__(
            css_classes=["ws-container"],
            vexpand=False,
            spacing=4,
            child=child_content,
        )

    def _hyprland_transform(self, workspaces, active_workspace):
        buttons = []
        # Get all workspace IDs (both existing and persistent)
        all_workspace_ids = set(ws.id for ws in workspaces if ws.id > 0) | set(
            PERSISTENT_WORKSPACES
        )
        # Sort all workspace IDs numerically
        sorted_workspace_ids = sorted(all_workspace_ids)

        for ws_id in sorted_workspace_ids:
            existing_workspace = next((ws for ws in workspaces if ws.id == ws_id), None)
            if existing_workspace:
                buttons.append(workspace_button(existing_workspace))
            elif ws_id in PERSISTENT_WORKSPACES:
                is_active = active_workspace and active_workspace.id == ws_id
                buttons.append(
                    create_persistent_workspace_button(ws_id, is_active, False)
                )

        return buttons

    def _niri_transform(self, workspaces):
        buttons = []
        # Get the monitor name properly - convert int to string if needed
        monitor_name = str(self.monitor_name) if isinstance(self.monitor_name, int) else self.monitor_name
        
        # For Niri, if no specific monitor filtering is needed, show all workspaces
        # or filter by the active output if needed
        active_output = niri.active_output
        relevant_workspaces = [
            ws for ws in workspaces 
            if ws.idx > 0 and (not monitor_name or ws.output == active_output)
        ]
        
        # Get existing workspaces indexed by their idx
        existing_workspaces = {ws.idx: ws for ws in relevant_workspaces}
        
        # Get all workspace IDs (both existing and persistent)
        all_workspace_ids = set(existing_workspaces.keys()) | set(PERSISTENT_WORKSPACES)
        # Sort all workspace IDs numerically
        sorted_workspace_ids = sorted(all_workspace_ids)

        for ws_id in sorted_workspace_ids:
            existing_workspace = existing_workspaces.get(ws_id)
            if existing_workspace:
                buttons.append(workspace_button(existing_workspace))
            elif ws_id in PERSISTENT_WORKSPACES:
                buttons.append(create_persistent_workspace_button(ws_id, False, False))

        return buttons
