from dev_agent.tools.shell import ShellTool
from dev_agent.tools.filesystem import FileSystemTool
from dev_agent.tools.project_analyzer import ProjectAnalyzerTool
from dev_agent.tools.code_editor import CodeEditorTool

TOOLS = [
    ShellTool(),
    FileSystemTool(),
    ProjectAnalyzerTool(),
    CodeEditorTool(),
]
