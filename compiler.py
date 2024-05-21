import sys
import getopt
import interfacing_parser
from errors import error_message
from lexer_parser import parser
from symbols import ASTSymbolVisitor
from type_checking import ASTTypeCheckingVisitor
from ast_printer import ASTTreePrinterVisitor
from label_generation import ASTLabelGeneratorVisitor
from code_generation import ASTCodeGenerationVisitor
from emit import Emit

__version__ = "0.5.7"

# MAIN
def compiler(showSource, showAST, input_file, output_file):
    """This function goes through the classic phases of a modern compiler,
    each phase organized in its own module. The phases are:

    parsing:
        handled using the ply package - the parser module includes a lexer,
        and it builds an abstract syntax tree (AST).

    symbol collection:
        collects function, parameter, classes and variables names, and stores these
        in a symbol table. It also handles adding types to AST nodes.
    
    Type checking:
        checks variables type are defiend in the case of classes. Function type matching
        the type of the return expression. Array elements match type of array. Type of 
        expression matches variable it is assinged to. 

    Label generation:
        generates labels for the identifiers, temp variables, attributes, etc. and stores
        them in a mix of the symbol table along with the variable it belongs to and the
        AST node which generates the label.

    code generation:
        from the AST and symbol table, instructions are produced in an intermediate
        representation which mimic the final C code quite closely.

    emit:
        the slightly abstract instruction forming the intermediate code is transformed to C code.
    """

    # Read and verify ASCII input:
    encodingError = False
    try:
        if input_file:
            with open(input_file) as f:
                text = f.read()
        else:
            text = sys.stdin.read()
        try:
            text.encode("ascii")
        except UnicodeEncodeError:  # Check for non-ascii
            encodingError = True
    except UnicodeDecodeError:  # Check for unicode
        encodingError = True
    if encodingError:
        error_message("Set-Up", "The input is not in ASCII.", 1)

    # Parse input text:
    parser.parse(text)

    # the_progrm is the resulting AST:
    the_program = interfacing_parser.the_program

    if showSource or showAST:
        if showAST:
            # Print AST tree in dot format:
            pp = ASTTreePrinterVisitor()

        the_program = the_program.body  # Remove artificial outer global.
        the_program.accept(pp)
        return pp.getPrettyProgram()
    else:
        # Collect names of functions, parameters, and local variables:
        symbols_collector = ASTSymbolVisitor()
        the_program.accept(symbols_collector)

        # Type check use of functions, parameters, local variables, classes, arrays:
        type_checker = ASTTypeCheckingVisitor()
        the_program.accept(type_checker)

        # Generate Labels for variables, functions, methods, attributes
        label_generator = ASTLabelGeneratorVisitor()
        the_program.accept(label_generator)

        # Generate intermediate code:
        intermediate_code_generator = ASTCodeGenerationVisitor()
        the_program.accept(intermediate_code_generator)
        intermediate_code = intermediate_code_generator.get_code()

        # Emit the target code:
        emitter = Emit(intermediate_code)
        emitter.emit()
        code = emitter.get_code()

        return code

def main(argv):
    usage = f"Usage: {sys.argv[0]} [-hvsm] [-i source_file] [-o target_file]"
    help_text = """
    -h  Print this help text.

    -v  Print the version number.

    -s  Print back the parsed source code instead of target code.

    -a  Print the AST in dot format instead of target code.

    -i source_file  Set source file; default is stdin.

    -o target_file  Set target file; default is stdout.
    """
    input_file = ""
    output_file = ""
    show_source = False
    show_ast = False
    try:
        opts, args = getopt.getopt(argv, "hsamvi:o:")
    except getopt.GetoptError:
        print(usage)
        sys.exit(1)
    for opt, arg in opts:
        match opt:
            case "-h":
                print(usage)
                print(help_text)
                sys.exit(0)
            case "-v":
                print(__version__)
                sys.exit(0)
            case "-s":
                show_source = True
            case "-a":
                show_ast = True
            case "-i":
                input_file = arg
            case "-o":
                output_file = arg
    result = compiler(show_source, show_ast, input_file, output_file)
    if output_file:
        f = open(output_file, "w")
        f.write(result)
        f.close()
    else:
        print(result)

if __name__ == "__main__":
    main(sys.argv[1:])
