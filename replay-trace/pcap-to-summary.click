define($INsrcmac b8:83:03:6f:43:11)
define($RAW_INsrcmac b883036f4311)

define($INdstmac 00:00:00:00:00:00)
define($RAW_INdstmac 000000000000)


fdIN :: FromDump($traceIN, STOP true, TIMING 1, TIMING_FNT "100", END_AFTER 0, ACTIVE true, BURST 1);
tdIN :: ToIPSummaryDump($traceOUT, BINARY true, FIELDS timestamp eth_src eth_dst ip_src ip_dst sport dport ip_len ip_proto eth_type);

fdIN
    -> MarkIPHeader(OFFSET 14)
    -> tdIN;

DriverManager(
    pause,
    print "ALL DONE...! :)",
    stop
);
