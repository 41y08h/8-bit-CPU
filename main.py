# Control bits
# INSTRUCTION   STEP    FLAG    HLT  MI  RI  RO  IO  II  AI  AO  EO  SU  BI  OI  CE  CO  J  FI


HLT = 0
MI = 1
RI = 2
RO = 3
IO = 4
II = 5
AI = 6
AO = 7
EO = 8
SU = 9
BI = 10
OI = 11
CE = 12
CO = 13
J = 14
FI = 15


instructions = {
    "NOP": [],
    "LDA": [
        [IO, MI],
        [RO, AI],
    ],
    "ADD": [
        [IO, MI],
        [RO, BI],
        [EO, AI, FI],
    ],
    "SUB": [
        [IO, MI],
        [RO, BI],
        [SU, EO, AI, FI],
    ],
    "STA": [
        [IO, MI],
        [AO, RI],
    ],
    "LDI": [
        [IO, AI],
    ],
    "OUT": [
        [AO, OI],
    ],
    "JMP": [
        [IO, J],
    ],
    "JZ": [
        {"1X": [IO, J]},
    ],
    "JC": [
        {"X1": [IO, J]},
    ],
    "HLT": [
        [HLT],
    ],
}


def binary_to_decimal(binary):
    return int(str(binary), 2)


def decimal_to_binary(decimal, num_bits=8):
    if decimal < 0 or decimal >= 2**num_bits:
        raise ValueError(
            f"Input must be a decimal number between 0 and {2 ** num_bits - 1}."
        )

    binary = bin(decimal)[2:].zfill(num_bits)
    return binary


def binary_to_hex(binary):
    return "{:x}".format(int(binary, 2))


def binary_wildcard_combinations(string):
    wildcard_count = string.count("X")  # Count the number of wildcard characters
    if wildcard_count == 0:
        return [string]  # Return the input string as the only combination

    combinations = []

    # Generate all possible combinations using binary numbers
    for i in range(2**wildcard_count):
        binary = bin(i)[2:].zfill(
            wildcard_count
        )  # Convert the decimal number to binary

        # Replace wildcard characters with binary digits in the string
        combination = list(string)
        for digit in binary:
            combination[combination.index("X")] = digit

        combinations.append("".join(combination))

    return combinations


def ucode_to_control_word_binary(array):
    result = ["0"] * 16  # Initialize result with all zeros

    for num in array:
        if num >= 0 and num <= 15:
            result[num] = "1"  # Set positions to 1 for numbers in the array

    return "".join(result)


def create_memory_image(instructions_bin, max_items=16):
    result = ["0" for i in range(max_items)]
    for instruction_bin in instructions_bin:
        address_bin, control_value_bin = instruction_bin
        # ROM image needs to be created in hexadecimal
        idx = binary_to_decimal(address_bin)
        result[idx] = binary_to_hex(control_value_bin)

    return result


def write_rom_image_to_file(array, file_path):
    with open(file_path, "w") as file:
        file.write("v2.0 raw\n")
        for i in range(0, len(array), 16):
            line = " ".join(array[i : i + 16])
            file.write(line + "\n")


def read_program(file_path):
    instructions = []
    data = {}

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Check if the line contains a label
            if ":" in line:
                label, value = line.split(":")
                label = label.strip()
                value = value.strip()
                data[label] = value
            else:
                instructions.append(line)

    return instructions, data


def generate_program_binary(file_path):
    coded_instructions, data = read_program(file_path)

    result = []
    # Process instructions
    for i, coded_instruction in enumerate(coded_instructions):
        instruction_parts = coded_instruction.split(" ")
        instruction_name = instruction_parts[0]
        mem_location = int(instruction_parts[1]) if len(instruction_parts) == 2 else 0

        if instruction_name not in instructions:
            raise ValueError("Invalid instruction: %s" % instruction_name)

        if mem_location not in range(16):
            raise ValueError("Invalid memory location: %s" % mem_location)

        # Opcode is the index of the instruction in the instructions dictionary
        opcode_decimal = list(instructions.keys()).index(instruction_name)
        opcode_bin = decimal_to_binary(opcode_decimal, num_bits=4)
        mem_location_bin = decimal_to_binary(mem_location, num_bits=4)
        address_bin = decimal_to_binary(i, num_bits=4)

        result.append((address_bin, opcode_bin + mem_location_bin))

    # Process data section
    for label, value in data.items():
        if label.isdigit() and int(label) in range(16):
            mem_location = int(label)
            value = int(value)

            if value not in range(256):
                raise ValueError(
                    "Invalid value for memory location %s: %s" % (mem_location, value)
                )

            mem_location_bin = decimal_to_binary(mem_location, num_bits=4)
            value_bin = decimal_to_binary(value, num_bits=8)

            result.append((mem_location_bin, value_bin))

    return result


def generate_lookup_table(instructions):
    result = []
    for ins_idx, ins_name in enumerate(instructions):
        opcode_bin = decimal_to_binary(ins_idx, num_bits=4)

        # Add fetch-cycle ucodes to every instruction
        ucodes = [
            [CO, MI],
            [RO, II, CE],
        ] + instructions[ins_name]

        for u_idx, ucode in enumerate(ucodes):
            isFlagsConditional = isinstance(ucode, dict)
            step_bin = decimal_to_binary(u_idx, num_bits=3)

            if isFlagsConditional:
                for flag, ucode_flag in ucode.items():
                    control_word_bin = ucode_to_control_word_binary(ucode_flag)

                    result = result + [
                        # Address of ROM, control word binary
                        (ins_name, opcode_bin, step_bin, flag, control_word_bin)
                    ]
            else:
                flag = "XX"
                control_word_bin = ucode_to_control_word_binary(ucode)

                result = result + [
                    # Address of ROM, control word binary
                    (ins_name, opcode_bin, step_bin, flag, control_word_bin)
                ]

    return result


def create_instructions_binary(lookup_table):
    result = []
    for instruction in lookup_table:
        name, opcode_bin, step_bin, flag, control_word_bin = instruction

        for flag_bin in binary_wildcard_combinations(flag):
            result = result + [
                # Address of ROM, control word binary
                (opcode_bin + step_bin + flag_bin, control_word_bin)
            ]

    return result


if __name__ == "__main__":
    # Generage firmware
    table = generate_lookup_table(instructions)
    ins_bin = create_instructions_binary(table)
    rom_image = create_memory_image(ins_bin, max_items=2**9)
    write_rom_image_to_file(rom_image, "bin/firmware.bin")
    print("Firmware image generated successfully. \nHere's the opcode binaries -->")

    for instruction_name, instruction_details in instructions.items():
        opcode = list(instructions.keys()).index(instruction_name)
        opcode_binary = bin(opcode)[2:].zfill(4)
        print(f"{instruction_name}: {opcode_binary}")

    # Generate Program
    program_bin = generate_program_binary("program")
    rom_image = create_memory_image(program_bin, max_items=16)
    write_rom_image_to_file(rom_image, "bin/program.bin")
    print("\nProgram image generated successfully.")
