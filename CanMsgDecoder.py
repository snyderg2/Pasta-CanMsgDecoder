import camelot
import re
import argparse
import matplotlib.pyplot as plt
import os
import pandas as pd
import pickle
import copy

class CanMsgMetadata:
    def __init__(self, can_id, io, data_loc, period_ms, description):
        self.can_id = can_id
        self.metadata = dict()
        self.metadata["io"] = io
        self.metadata["can_id"] = can_id
        self.metadata["data_loc"] = data_loc
        self.metadata["period_ms"] = period_ms
        self.metadata["description"] = description.replace("\n", "")

    def __str__(self):
        return "ID {}:: IO->{}; data_loc->{}; period->{}ms\nDescription: {}\n" \
            .format(self.can_id, self.metadata["io"], self.metadata["data_loc"], self.metadata["period_ms"],
                    self.metadata["description"])

    def __repr__(self):
        return self.__str__()

    def get(self, attribute_str):
        return self.metadata[attribute_str]


class CanDecodedMsg:
    def __init__(self, can_id, description, time_s, value_lst):
        self.can_id = can_id
        self.name = re.search('\s?\w\D+\s', description).group()
        self.desc = re.search('\d+.*', description).group()
        self.time_s = float(time_s)
        self.value_lst = value_lst

    def __str__(self):
        return "{}: CanId=={}, values=={}, time=={}, value_key=={}".format(self.name, self.can_id, self.value_lst,
                                                                           self.time_s, self.desc)

    def __repr__(self):
        return str(self)

    def get_values(self):
        return self.value_lst

    def get_time(self):
        return self.time_s

    def get_time_and_values(self):
        return [[self.get_time()], self.get_values()]

    def get_can_id(self):
        return self.can_id

    def get_name(self):
        return self.name

    def get_can_id(self):
        return self.can_id

    def get_value_description(self):
        return self.desc


class CanMsgDecoder:
    byte_len = 2
    one_byte_symbols = ["DB"]
    two_bytes_symbols = ["DH", "DL"]
    four_bytes_symbols = ["HH", "HL", "LH", "LL"]

    def __init__(self, can_metadata):
        self.metadata = can_metadata

    def get_payload_values(self, can_id, can_payload, debug=False):
        can_metadata = self.metadata[can_id]
        data_loc_str = can_metadata.get("data_loc")

        data_locs = data_loc_str.split()
        byte_list = [can_payload[byte:byte + self.byte_len] for byte in range(0, len(can_payload), self.byte_len)]
        value_lst = self.aggregate_bytes(data_locs, byte_list, debug)
        return value_lst

    def aggregate_bytes(self, data_locs, byte_list, debug=False):
        byte_value = 0
        value = 0
        value_lst = []
        byte_symbols = []
        if any(sym in data_locs for sym in self.one_byte_symbols):
            byte_symbols = self.one_byte_symbols
        elif any(sym in data_locs for sym in self.two_bytes_symbols):
            byte_symbols = self.two_bytes_symbols
        elif any(sym in data_locs for sym in self.four_bytes_symbols):
            byte_symbols = self.four_bytes_symbols

        if debug:
            print(byte_symbols)

        if len(byte_symbols):
            byte_num = 0
            for sym in reversed(byte_symbols):
                byte = byte_list[data_locs.index(sym)]
                byte_value = int(byte, 16) << (byte_num * 8)
                value += byte_value
                if debug:
                    print("sym {} -> (byte 0x{} << {}*8) => {}".format(sym, byte, byte_num, byte_value))
                byte_num += 1
                if byte_num > 1 or sym in self.one_byte_symbols:
                    byte_num = 0
                    value_lst.insert(0, value)
                    value = 0
        if debug:
            print(value_lst)
        return value_lst

    def decode_msg_str(self, data_str, debug=False):
        log_values = data_str.split()
        time_s = log_values[0].replace("(", "").replace(")", "")
        canbus_id = log_values[1]
        can_data = log_values[2]
        can_id, can_data = can_data.split('#', 1)
        if debug:
            print("time_s({}), canbus_id({}), can_id({}), payload({})".format(time_s, canbus_id, can_id, can_data))

        # todo: might want to handle HH HL LH LL by treating as two decoded messages
        value_lst = self.get_payload_values(can_id=can_id, can_payload=can_data, debug=debug)
        can_metadata = self.metadata[can_id]
        description = can_metadata.get("description")
        decoded_msg = CanDecodedMsg(can_id, description, time_s, value_lst)
        return decoded_msg


def get_msg_metadata_dict(msg_data_tables, debug=False):
    msg_metadata_dict = dict()
    col_ndx = dict()
    first_table_header = True
    for msg_table in msg_data_tables:
        for index, row in msg_table.df.iterrows():
            if first_table_header and "I/O" in row[0]:
                first_table_header = False
                for index, val in row.iteritems():
                    if "I/O" in val:
                        col_ndx["io"] = index
                    elif "CAN-ID" in val:
                        col_ndx["can_id"] = index
                    elif "Data Location" in val:
                        col_ndx["data_loc"] = index
                    elif "Period" in val:
                        col_ndx["period_ms"] = index
                    elif "Description" in val:
                        col_ndx["description"] = index
                print(col_ndx)
                continue
            elif "I/O" in row[0]:
                continue

            can_id = row[col_ndx["can_id"]]
            can_msg = CanMsgMetadata(can_id, row[col_ndx["io"]], row[col_ndx["data_loc"]], row[col_ndx["period_ms"]],
                                     row[col_ndx["description"]])
            if debug:
                print(can_msg)
            msg_metadata_dict[can_id] = can_msg

    return msg_metadata_dict


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-spec', '--can_spec', dest='can_spec', type=str, required=True, help="CAN specification that contains how to understand CAN messages")
    parser.add_argument('-pgs', '--spec_pgs', dest='spec_pgs', type=str, required=True, help="CAN specification pages that contains the table for parsing CAN messages")
    parser.add_argument('-bin_out', '--bin_outfile', dest='bin_outfile', type=str, required=False, default=None, help="bin file for the dictionary of decoded messages to be put into. can be used for loading for machine learning")
    parser.add_argument('-parse_f', '--parse_file', dest='parse_file', type=str, required=True, help="log file that is to be parsed by the can decoder")
    parser.add_argument('-can_ids', '--wanted_can_ids', dest='wanted_can_ids', type=str, default='all', required=False, help="filter for which canids pull from logfile, good for isolating messages. default is all. comma seperated list of id's in hex ej 01A,2BC,321")
    parser.add_argument('-max_line', '--max_line_cnt', dest='max_line_cnt', type=int, default=0, required=False, help="max line count of log file that will be parsed. default is to parse all")
    parser.add_argument('-plot', '--plot_data', dest='plot_data', action="store_true", default=False, required=False, help="show plots of the wanted data for the specified duration")
    parser.add_argument('-corr', '--print_corr', dest='print_corr', action="store_true", default=False, required=False, help="print tables for pearson and spearman correlations. note: if corr table has nans it is due to no specified can messages existed in log")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    msg_spec_file = args.can_spec
    pckl_outfile = args.bin_outfile
    parse_filename = args.parse_file
    filtered_can_ids = list()
    all_can_ids = False
    if args.wanted_can_ids == "all":
        all_can_ids = True
    else:
        filtered_can_ids = [s.strip().upper() for s in args.wanted_can_ids.split(",")]

    if not os.path.isfile(msg_spec_file) or not os.access(msg_spec_file, os.R_OK):
        print("ERROR: File --can_spec {} isn't a valid file or not readable".format(msg_spec_file))
        exit(-1)
    pasta_msg_table = camelot.read_pdf(msg_spec_file, pages=args.spec_pgs)
    #pasta_msg_table.export(csv_out_file, f='csv', compress=True)
    #pasta_msg_table[0].to_csv(csv_out_file)

    metadata = get_msg_metadata_dict(pasta_msg_table, debug=False)
    decoder = CanMsgDecoder(metadata)
    count = 1
    graph_dict = dict()
    with open(parse_filename) as parse_file:
        for line in parse_file:
            decoded_msg = decoder.decode_msg_str(line)
            can_id = decoded_msg.get_can_id()
            data = decoded_msg.get_name()
            if all_can_ids or can_id in filtered_can_ids:
                time_and_values = decoded_msg.get_time_and_values()
                time_and_values = [time_and_values[0][0], time_and_values[1][0]]
                if can_id not in graph_dict:
                    graph_dict[can_id] = list()
                    graph_dict[can_id].append(["time", data])
                graph_dict[can_id].append(time_and_values)
                if args.max_line_cnt:
                    count += 1
                    if count >= args.max_line_cnt:
                        break

    if args.print_corr:
        pd.set_option('display.max_columns', len(filtered_can_ids)+1)
        first_time = True
        for k, v in graph_dict.items():
            v_cp = copy.copy(v)
            time_col_name, col_name = v_cp.pop(0)
            col_name = str(k) #+ ": " + str(col_name)
            #time_stamps, values = map(list, zip(*v)) {time_col_name: time_stamps, col_name: values}
            if first_time:
                interpolated_df = pd.DataFrame(v_cp, columns=[time_col_name, col_name])
                first_time = False
            else:
                concat_df = pd.DataFrame(v_cp, columns=[time_col_name, col_name])
                interpolated_df = pd.concat([interpolated_df, concat_df], join="outer", sort=True, ignore_index=True)
                #interpolated_df = pd.merge_ordered(interpolated_df, concat_df, on=time_col_name, how="outer")
                #interpolated_df.merge(concat_df, how="outer", on=time_col_name) #pd.concat([interpolated_df, concat_df], join="outer", sort=True) #interpolated_df.join(concat_df) #pd.concat([interpolated_df, concat_df])
        interpolated_df[:1] = interpolated_df[:1].fillna(0)
        interpolated_df = interpolated_df.interpolate().set_index(time_col_name)
        spearman_df = interpolated_df.corr(method="spearman")
        print("spearman corr\n{}\n".format(spearman_df))
        pearson_df = interpolated_df.corr(method="pearson")
        print("pearson corr\n{}\n".format(pearson_df))

    if pckl_outfile is not None:
        pickle.dump(graph_dict, open(pckl_outfile, "wb"))


    if args.plot_data:
        for can_id in graph_dict:
            title = metadata[can_id].get("description")
            title = re.search('^((?:\S+\s+){2}\S+)', title).group().strip("()")
            data_list = graph_dict[can_id]
            legend = data_list.pop(0)
            df = pd.DataFrame(graph_dict[can_id], columns=["time", "values"])
            df.set_index("time", drop=True, inplace=True)
            df.plot(kind='line')
            plt.title(legend[-1])
        plt.show()
