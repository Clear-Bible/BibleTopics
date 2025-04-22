"""Internal code for working with Bible Topics."""

from pathlib import Path
import os

# the dotenv magic only works if your Python environment is running in
# the right directory
import dotenv

# use an environment variable if available
if not dotenv.load_dotenv():
    print("No .env file found")
clearrootenvar = os.getenv("CLEARROOT")
if clearrootenvar:
    CLEARROOT = Path(clearrootenvar)
else:
    CLEARROOT = Path.home() / "git/Clear-Bible"
    print(f"No environment variable for CLEARROOT: assuming {CLEARROOT}")

ROOT = Path(__file__).parent.parent
DATAPATH = ROOT / "data"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SYMPHONY_ATLAS_GRAPHQL_ENDPOINT = os.getenv("SYMPHONY_ATLAS_GRAPHQL_ENDPOINT")
assert (
    OPENAI_API_KEY
), "Could not initialize OPENAI_API_KEY: are you in the right directory?\n{os.getcwd()}"


__all__ = [
    "CLEARROOT",
    "ROOT",
    "DATAPATH",
    "OPENAI_API_KEY",
    "SYMPHONY_ATLAS_GRAPHQL_ENDPOINT",
]
