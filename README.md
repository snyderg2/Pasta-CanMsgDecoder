# Pasta-CanMsgDecoder
CAN message decoder for parsing log files that contain pasta can framework. You will need to provide the spec and table 
of can messages used for cyphering. There is a help option provided by the program with the following output. You will
need to have the specification path along with the pages where the can message data table is located. For pasta 
framework it is pages 24-32. See example commands on how to run below

usage: CanMsgDecoder.py [-h] -spec CAN_SPEC -pgs SPEC_PGS
                        [-bin_out BIN_OUTFILE] -parse_f PARSE_FILE
                        [-can_ids WANTED_CAN_IDS] [-max_line MAX_LINE_CNT]
                        [-plot] [-corr]

optional arguments:
  -h, --help            show this help message and exit
  -spec CAN_SPEC, --can_spec CAN_SPEC
                        CAN specification that contains how to understand CAN
                        messages
  -pgs SPEC_PGS, --spec_pgs SPEC_PGS
                        CAN specification pages that contains the table for
                        parsing CAN messages
  -bin_out BIN_OUTFILE, --bin_outfile BIN_OUTFILE
                        bin file for the dictionary of decoded messages to be
                        put into. can be used for loading for machine learning
  -parse_f PARSE_FILE, --parse_file PARSE_FILE
                        log file that is to be parsed by the can decoder
  -can_ids WANTED_CAN_IDS, --wanted_can_ids WANTED_CAN_IDS
                        filter for which canids pull from logfile, good for
                        isolating messages. default is all. comma seperated
                        list of id's in hex ej 01A,2BC,321
  -max_line MAX_LINE_CNT, --max_line_cnt MAX_LINE_CNT
                        max line count of log file that will be parsed.
                        default is to parse all
  -plot, --plot_data    show plots of the wanted data for the specified
                        duration
  -corr, --print_corr   print tables for pearson and spearman correlations.
                        note: if corr table has nans it is due to no specified
                        can messages existed in log


Example Commands
CanMsgDecoder.py -spec Specifications.pdf -pgs 24-32 -parse_f pasta-candump.log -can_ids 01A,25c,1b1 -csv_out can_msgs.csv
CanMsgDecoder.py -spec Specifications.pdf -pgs 24-32 -parse_f pasta-candump.log -can_ids 01A,02F,058,024,039,043 -max_line 75000 -corr -plot -bin_out parsed_dict
CanMsgDecoder.py -spec Specifications.pdf -pgs 24-32 -parse_f pasta-candump.log -can_ids 043,183,19a -corr -plot -bin_out parsed_dict