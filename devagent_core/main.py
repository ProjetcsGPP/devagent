from devagent_core.core.bootstrap import Bootstrap
from devagent_core.interfaces.cli import DevAgentCLI


def main():
    bootstrap = Bootstrap().start()

    cli = DevAgentCLI(bootstrap)
    cli.start()


if __name__ == "__main__":
    main()