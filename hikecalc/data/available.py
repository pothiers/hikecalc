from glob import glob
from pathlib import Path

def datfiles():
    #!files = [str(Path(f).name) for f in glob(f'{Path(__file__).parent}/*.dat')]
    paths = [Path(f) for f in glob(f'{Path(__file__).parent}/*.dat')]
    #print(f'DAT Files available: {files}')
    return paths
