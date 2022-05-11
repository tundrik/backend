

class ViewerType:
    def __init__(
            self,
            *,
            pk,
            role,
            manager_id,
            guid,
            internal,
    ):
        self.pk = pk
        self.role = role
        self.manager_id = manager_id
        self.guid = guid
        self.internal = internal


class Bsv:
    def __init__(
            self,
            *,
            viewer: ViewerType
    ):
        self.viewer = viewer
