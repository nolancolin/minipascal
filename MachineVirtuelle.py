import AnalyseurLexical, TableSymboles

OPERATION = ["ADDI","SOUS","MULT","DIVI","MOINS","EMPI","CONT","LIRE","AFFE","ECRL","ECRC","ECRE","FINC","STOP","ALLE","ALSN"]
PILEX = []
TAILLE_MAX_MEM = 10000
PILOP = []
MEMVAR = {}
P_CODE = [-1] * TAILLE_MAX_MEM
CO = 0

def creer_fichier_code(nom : str) -> None:
    nom = nom.removesuffix("minipascal") + "cod"
    with open(nom, "w") as writer:
        writer.write(f"{len(MEMVAR)} mot(s) reserve(s) pour les variables globales.\n")
        idx = 0
        while idx < CO:
            instr = OPERATION[P_CODE[idx]]
            writer.write(f"{instr} ")
            match instr:
                case "EMPI":
                    writer.write(str(P_CODE[idx+1]))
                    idx+=2

                case "ECRC":
                    writer.write("'")
                    idx+=1
                    while P_CODE[idx] != 12:
                        writer.write(chr(P_CODE[idx]))
                        idx+=1
                    
                    writer.write(f"' {OPERATION[P_CODE[idx]]}")
                    idx+=1
                
                case "ALLE": 
                    writer.write(str(P_CODE[idx+1]))
                    idx+=2
                
                case "ALSN":
                    writer.write(str(P_CODE[idx+1]))
                    idx+=2

                case "STOP": return
                
                case _: idx+=1
            writer.write("\n")
    writer.close()

# ===== MACHINE VIRTUELLE =====

def interpreterWithFile(nom: str) -> None:
    nom = nom.removesuffix("minipascal") + "cod"
    with open(nom, "r") as reader:
        reader.readline()
        while (line := reader.readline()) != "EOF":
            instr = line[:4]
            match instr: 
                case "EMPI": 
                    PILEX.append(line[5])
                
                case "CONT": 
                    adr = int(PILEX.pop())
                    PILEX.append(MEMVAR[adr])
                
                case "ADDI":
                    b = int(PILEX.pop())
                    a = int(PILEX.pop())
                    PILEX.append(a + b)
                    
                case "SOUS":
                    b = int(PILEX.pop())
                    a = int(PILEX.pop())
                    PILEX.append(a - b)

                case "MULT":
                    b = int(PILEX.pop())
                    a = int(PILEX.pop())
                    PILEX.append(a * b)
                
                case "DIVI":
                    b = int(PILEX.pop())
                    if not b: return AnalyseurLexical.erreur(4)
                    a = int(PILEX.pop())
                    PILEX.append(a / b)
                
                case "MOIN":
                    a = int(PILEX.pop())
                    PILEX.append(-a)
                
                case "AFFE":
                    val = int(PILEX.pop())
                    adr = int(PILEX.pop())
                    MEMVAR[adr] = val

                case "LIRE":
                    adr = int(PILEX.pop())
                    read = input()
                    if not read.isnumeric(): return AnalyseurLexical.erreur(9)
                    MEMVAR[adr] = int(read)

                case "ECRE": 
                    print(PILEX.pop(), end="")

                case "ECRC":
                    i = 6
                    while line[i] != "'":
                        print(line[i],end="")
                        i += 1

                case "ECRL": print()
                
                # case "ALSN":

                case "STOP": return
    reader.close()

def interpreter() -> None:
    idx = 0
    while idx < CO:
        instr = OPERATION[P_CODE[idx]]
        
        match instr:
            case "EMPI":
                PILEX.append(P_CODE[idx+1])
                idx += 1

            case "CONT":
                adr = PILEX.pop()
                PILEX.append(MEMVAR[adr])

            case "ADDI":
                b = PILEX.pop()
                a = PILEX.pop()
                PILEX.append(a + b)
                
            case "SOUS":
                b = PILEX.pop()
                a = PILEX.pop()
                PILEX.append(a - b)

            case "MULT":
                b = PILEX.pop()
                a = PILEX.pop()
                PILEX.append(a * b)
            
            case "DIVI":
                b = PILEX.pop()
                if not b: return AnalyseurLexical.erreur(4)
                a = PILEX.pop()
                PILEX.append(a / b)
            
            case "MOIN":
                a = PILEX.pop()
                PILEX.append(-a)

            case "AFFE":
                val = PILEX.pop()
                adr = PILEX.pop()
                MEMVAR[adr] = val

            case "LIRE":
                adr = PILEX.pop()
                read = input()
                if not read.isnumeric(): return AnalyseurLexical.erreur(9)
                MEMVAR[adr] = int(read)

            case "ECRE": print(PILEX.pop(), end="")

            case "ECRC":
                while P_CODE[idx] != 12:
                    print(chr(P_CODE[idx+1]), end="")
                    idx += 1

            case "ECRL": print()

            case "STOP": break
        idx += 1