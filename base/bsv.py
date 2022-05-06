

class ViewerType:
    def __init__(
            self,
            *,
            pk,
            guid,
            internal,
    ):
        self.pk = pk
        self.guid = guid
        self.internal = internal


class Bsv:
    def __init__(
            self,
            *,
            viewer: ViewerType
    ):
        self.viewer = viewer
