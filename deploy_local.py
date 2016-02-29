import plumbum as pb

def main():
    pb.local['ct-mksetup']()
    pb.local['ct-mkvenv']('-e')
    pb.local['venv/bin/py.test']()

main()