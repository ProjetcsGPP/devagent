class ProjectIndexAdapter:
    def __init__(self, project_index):
        self._index = project_index.index

    def list_files(self):
        return self._index

    def count_files(self):
        return len(self._index)
    
    def get_index(self):
        return self.index