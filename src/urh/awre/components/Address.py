from collections import defaultdict

import numpy as np
from urh import constants
from urh.awre.CommonRange import CommonRange

from urh.awre.components.Component import Component


class Address(Component):
    MIN_ADDRESS_LENGTH = 8  # Address should be at least one byte

    def __init__(self, participant_lut, xor_matrix, priority=2, predecessors=None, enabled=True, backend=None):
        super().__init__(priority, predecessors, enabled, backend)
        self.xor_matrix = xor_matrix
        self.participant_lut = participant_lut

    def _py_find_field(self, messages):

        raise NotImplementedError("")

        # Cluster participants
        equal_ranges_per_participant = defaultdict(list)

        alignment = 8

        # Step 1: Find equal ranges for participants by evaluating the XOR matrix participant wise
        for i, row in enumerate(rows):
            participant = self.participant_lut[row]
            for j in range(i, len(rows)):
                other_row = rows[j]
                if self.participant_lut[other_row] == participant:
                    xor_vec = self.xor_matrix[row, other_row][self.xor_matrix[row, other_row] != -1]
                    for rng_start, rng_end in column_ranges:
                        start = 0
                        # The last 1 marks end of seqzence, and prevents swalloing long zero sequences at the end
                        cmp_vector = np.append(xor_vec[rng_start:rng_end], 1)
                        for end in np.where(cmp_vector == 1)[0]:
                            if end - start >= self.MIN_ADDRESS_LENGTH:
                                equal_range_start = alignment * ((rng_start + start) // alignment)
                                equal_range_end = alignment * ((rng_start + end) // alignment)
                                bits = "".join(map(str, bitvectors[row][equal_range_start:equal_range_end]))

                                cr = next((cr for cr in equal_ranges_per_participant[participant] if
                                          cr.start == equal_range_start and cr.end == equal_range_end
                                          and cr.bits == bits), None)
                                if cr is None:
                                    cr = CommonRange(equal_range_start, equal_range_end, bits)
                                    equal_ranges_per_participant[participant].append(cr)
                                cr.messages.add(row)
                                cr.messages.add(other_row)

                            start = end + alignment

        print(equal_ranges_per_participant)

        print(constants.color.BOLD + "Result after Step 1" +constants.color.END)
        self.__print_ranges(equal_ranges_per_participant)

        # Step 2: Now we want to find our address candidates.
        # Step 2.a: Cluster the ranges based on their byte length
        for parti, ranges in equal_ranges_per_participant.items():
            hex_values = [common_range.hex_value for common_range in ranges]
            hex_values.sort(key=len)
            print(hex_values)



        #self.__print_clustered(clustered_addresses)

        # Now we search for ranges that are common in a cluster and contain different bit values. There are two possibilities:
        #   1) If the protocol contains ACKs, these different values are the addresses or at least good candidates for them
        #   2) If the protocol does not contain ACKs, these values contain both addresses and need to be splitted against each other
        # We assume, that the protocol contains ACKs and if we do not find any use the strategy from 2).



        #print(clustered_addresses)
        # Step 2: Align sequences together (correct bit shifts, align to byte)


        raise NotImplementedError("Todo")

    def __print_clustered(self, clustered_addresses):
        for bl in sorted(clustered_addresses):
            print(constants.color.BOLD + "Byte length " + str(bl) + constants.color.END)
            for (start, end), bits in sorted(clustered_addresses[bl].items()):
                print(start, end, bits)

    def __print_ranges(self, equal_ranges_per_participant):
        for parti in sorted(equal_ranges_per_participant):
            print("\n" + constants.color.UNDERLINE + str(parti.name) + " (" + parti.shortname+ ")" + constants.color.END)
            address1 = "000110110110000000110011"
            address2 = "011110001110001010001001"

            assert len(address1) % 8 == 0
            assert len(address2) % 8 == 0

            print("address1", constants.color.BLUE, address1 + " (" +hex(int("".join(map(str, address1)), 2)) +")", constants.color.END)
            print("address2", constants.color.GREEN, address2 + " (" + hex(int("".join(map(str, address2)), 2)) + ")",
                  constants.color.END)

            print()

            for common_range in sorted(equal_ranges_per_participant[parti]):
                assert isinstance(common_range, CommonRange)
                bits_str = common_range.bits
                format_start = ""
                if address1 in bits_str and address2 not in bits_str:
                    format_start = constants.color.BLUE
                if address2 in bits_str and address1 not in bits_str:
                    format_start = constants.color.GREEN
                if address1 in bits_str and address2 in bits_str:
                    format_start = constants.color.RED + constants.color.BOLD

                # For Bob the adress 1b60330 is found to be 0x8db0198000 which is correct,
                # as it starts with a leading 1 in all messages.
                # This is the last Bit of e0003 (Broadcast) or 78e289  (Other address)
                # Code to verify: hex(int("1000"+bin(int("1b6033",16))[2:]+"000",2))
                # Therefore we need to check for partial bits inside the address candidates to be sure we find the correct ones
                occurences = len(common_range.messages)
                print(common_range.start, common_range.end,
                      "({})\t".format(occurences),
                      format_start + common_range.hex_value + "\033[0m", common_range.byte_len,
                      bits_str, "(" + ",".join(map(str, common_range.messages)) + ")")


