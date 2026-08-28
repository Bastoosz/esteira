import os, sys
from pathlib import Path
BASE = Path(os.environ.get("ESTEIRA_DIR", Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(BASE))
import config
from esteira.demanda import Demanda

def demanda_atual():
    id_ = os.environ.get("ESTEIRA_DEMANDA")
    if not id_:
        print("erro: ESTEIRA_DEMANDA não definida. Rode pelo worker.", file=sys.stderr)
        sys.exit(2)
    return Demanda(id_)
