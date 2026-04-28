class ProjectSources:
    """
    Registra múltiplos repositórios externos
    para análise do DevAgent.
    """

    def __init__(self):
        self.sources = {
            "backend": "https://github.com/ProjectsGPP/gpp_plataform2.0",
            "frontend": "https://github.com/ProjectsGPP/gpp_plataform_front",
        }

    def list_sources(self):
        return self.sources

    def add_source(self, name: str, url: str):
        self.sources[name] = url