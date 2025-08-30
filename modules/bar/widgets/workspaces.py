from ignis import widgets
from ignis.services.hyprland import HyprlandService, HyprlandWorkspace

hyprland = HyprlandService.get_default()

# TODO: Config support and Styling
persistent = True
persistent_ids = [1, 2, 3, 9, 10]

custom_labels = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
}


class WorkspaceButton(widgets.Button):
    def __init__(
        self,
        workspace: HyprlandWorkspace = None,
        workspace_id: int = None,
        label=None,
        is_active=False,
    ) -> None:
        if workspace:
            click_action = lambda x: workspace.switch_to()
            display_label = label or custom_labels.get(workspace.id, str(workspace.id))
        else:
            click_action = lambda x: hyprland.switch_to_workspace(workspace_id)
            display_label = label or custom_labels.get(workspace_id, str(workspace_id))

        super().__init__(
            label=display_label,
            css_classes=["workspace", "unset"],
            on_click=click_action,
            halign="start",
            valign="center",
        )
        if is_active:
            self.add_css_class("active")


def scroll_workspaces(direction: str) -> None:
    current = hyprland.active_workspace.id

    if persistent:
        workspace_range = persistent_ids

        try:
            current_index = workspace_range.index(current)
        except ValueError:
            target = workspace_range[0]
            hyprland.switch_to_workspace(target)
            return

        if direction == "up":
            target_index = (current_index - 1) % len(workspace_range)
        else:
            target_index = (current_index + 1) % len(workspace_range)

        target = workspace_range[target_index]
        hyprland.switch_to_workspace(target)
    else:
        existing_workspaces = sorted([ws.id for ws in hyprland.workspaces])

        if not existing_workspaces:
            return

        try:
            current_index = existing_workspaces.index(current)
        except ValueError:
            target = existing_workspaces[0]
            hyprland.switch_to_workspace(target)
            return

        if direction == "up":
            target_index = (current_index - 1) % len(existing_workspaces)
        else:
            target_index = (current_index + 1) % len(existing_workspaces)

        target = existing_workspaces[target_index]
        hyprland.switch_to_workspace(target)


class Workspaces(widgets.Box):
    def __init__(self):
        if hyprland.is_available:
            child = [
                widgets.EventBox(
                    on_scroll_up=lambda x: scroll_workspaces("up"),
                    on_scroll_down=lambda x: scroll_workspaces("down"),
                    css_classes=["workspaces"],
                    child=hyprland.bind_many(
                        ["workspaces", "active_workspace"],
                        transform=self._create_workspace_buttons,
                    ),
                )
            ]
        else:
            child = []
        super().__init__(child=child)

    def _create_workspace_buttons(self, workspaces, active_workspace):
        if persistent:
            existing_workspace_ids = {ws.id for ws in workspaces}

            buttons = []
            for workspace_id in persistent_ids:
                is_active = active_workspace and active_workspace.id == workspace_id
                exists = workspace_id in existing_workspace_ids

                label = custom_labels.get(workspace_id, str(workspace_id))

                button = WorkspaceButton(
                    workspace_id=workspace_id, label=label, is_active=is_active
                )

                if not exists:
                    button.add_css_class("empty")

                buttons.append(button)

            return buttons
        else:
            return [
                WorkspaceButton(
                    workspace=workspace,
                    label=custom_labels.get(workspace.id, str(workspace.id)),
                    is_active=active_workspace and active_workspace.id == workspace.id,
                )
                for workspace in workspaces
            ]
