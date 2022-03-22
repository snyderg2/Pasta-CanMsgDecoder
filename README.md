# Pasta-CanMsgDecoder
CAN message decoder for parsing log files that contain pasta can framework. You will need to provide the spec and table of can messages used for cyphering

Example Command
CanMsgDecoder.py -spec Specifications.pdf -pgs 24-32 -parse_f pasta-candump.log -can_ids 01A,25c,1b1 -csv_out can_msgs.csv
