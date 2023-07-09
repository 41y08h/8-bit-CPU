# Control bits
# HLT MI RI RO IO II AI AO EO SU BI OI CE CO J -

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


instructions = {
    "NOP": {
        "microcodes": [],
    },
    "LDA": {
        # Loads the value from the given memory location into the A Register
        # eg. LDA 15
        "microcodes": [
            [IO, MI],
            [RO, AI],
        ],
    },
    "ADD": {
        # Adds the value from the given memory location to the A Register
        "microcodes": [
            [IO, MI],
            [RO, BI],
            [EO, AI],
        ],
    },
    "OUT": {
        # Transfers the value from the A Register to the Output Register
        "microcodes": [
            [AO, OI],
        ],
    },
}


def microcode_to_control_value_binary(array):
    result = ["0"] * 16  # Initialize result with all zeros

    for num in array:
        if num >= 0 and num <= 15:
            result[num] = "1"  # Set positions to 1 for numbers in the array

    return "".join(result)


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


def generate_instructions_binary(instructions):
    instructions_bin = []
    for instruction_idx, instruction_name in enumerate(instructions):
        # Instruction
        instruction = instructions[instruction_name]
        # Add fetch-cycle microcode to every instruction
        fetch_microcodes = [
            [CO, MI],
            [RO, II, CE],
        ]
        microcodes = fetch_microcodes + instruction["microcodes"]
        instruction_opcode_bin = decimal_to_binary(instruction_idx, num_bits=4)

        for microcode_idx, microcode in enumerate(microcodes):
            step_bin = decimal_to_binary(
                microcode_idx,
                num_bits=3,
            )
            control_value_bin = microcode_to_control_value_binary(microcode)
            instructions_bin = instructions_bin + [
                # Address (of Control Unit ROM), control value (in binary)
                [instruction_opcode_bin + step_bin, control_value_bin]
            ]
    return instructions_bin


def create_rom_image(instructions_bin):
    result = ["0000" for i in range(8 * 16)]
    for instruction_bin in instructions_bin:
        address_bin = instruction_bin[0]
        control_value_bin = instruction_bin[1]

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


instructions_bin = generate_instructions_binary(instructions)
rom_image = create_rom_image(instructions_bin)


if __name__ == "__main__":
    # write_rom_image_to_file(rom_image, "control_firmware.bin")
    # print("Control firmware generated successfully.")

    coded_instructions, data = read_program("adder")

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

    print(result)
