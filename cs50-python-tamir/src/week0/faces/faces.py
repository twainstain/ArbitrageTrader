def convert(str:str):
    return str.replace(":)", "🙂").replace(":(", "🙁")

def main():
    input = input("what's is your input ?")
    convert(input)

main()