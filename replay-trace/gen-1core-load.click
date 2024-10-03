d :: DPDKInfo(200000)

define($bout 32)
define($INsrcmac b8:83:03:6f:43:11)
define($RAW_INsrcmac b883036f4311)

define($INdstmac 00:00:00:03:00:00)
define($RAW_INdstmac b883036f3214)

define($ignore 0)
define($replay_count 1)
define($port 0000:11:00.0)
define($quick true)
define($txverbose 99)
define($rxverbose 99)

elementclass MyNull { [0-0]=>[0- 0 ]; };

// JiffieClock()
fdIN0 :: FromIPSummaryDump(/mnt/traces/emil/summary/pcap_summary.sum, TIMES $replay_count, TIMING 0, TIMESTAMP 0, ZERO false, BURST 1, STOP true, FIELDS timestamp eth_src eth_dst ip_src ip_dst sport dport ip_len ip_proto eth_type);


tdIN :: ToDPDKDevice($port, BLOCKING true, VERBOSE $txverbose, NDESC 1024, IPCO true, BURST 1)

elementclass NoTimestampDiff { $a, $b, $c, $d |
input -> output;
Idle->[1]output;
}

elementclass Numberise { $magic |
    input-> Strip(14)
     -> check :: MarkIPHeader
     -> NumberPacket(OFFSET 28, NET_ORDER true)
    -> ResetIPChecksum() -> Unstrip(14) -> output
}

ender :: Script(TYPE PASSIVE,
                print "Limit of 40000000 reached",
                stop,
                stop);
 rr :: MyNull;

fdIN0 -> limit0   :: Counter(COUNT_CALL 50000000 ender.run)-> unqueue0 ::  RatedUnqueue(200000, BURST 1)  -> [0]rr

elementclass Generator { $magic |
input

  -> MarkMACHeader
-> EnsureDPDKBuffer

  -> EnsureEther(0x0800, $INsrcmac, $INdstmac)
//  -> EtherRewrite($INsrcmac, $INdstmac)
  -> Pad
  -> Numberise($magic)
  -> avgSIN :: AverageCounter(IGNORE $ignore)

  -> output;
}

rr[0] -> gen0 :: Generator(\<5700>) -> tdIN;StaticThreadSched(fdIN0 0/1 , unqueue0 0/1)


receiveIN :: FromDPDKDevice($port, VERBOSE $rxverbose, MAC $INsrcmac, PROMISC true, PAUSE full, NDESC 1024, MAXTHREADS 1, MINQUEUES 1, NUMA false, RSS_AGGREGATE true, ACTIVE 1)

elementclass Receiver { $mac, $dir |
    input[0]
 -> c :: Classifier(-, 0/ffffffffffff)
    -> Strip(14)
    -> CheckIPHeader(CHECKSUM false)

-> magic :: {[0]-> RoundRobinSwitch(SPLITBATCH false)[0-0] => [0-0]output;Idle->[1]output;};

    c[1] //Not for this computer or broadcasts
    -> Discard;

magic[0] -> tsd0 :: NoTimestampDiff(gen0/rt, OFFSET 42, N 80002048, SAMPLE 10 ) -> Unstrip(14) ->  avg0 :: AverageCounterMP(IGNORE $ignore) -> Discard;  tsd0[1] -> Print('WARNING: Untimestamped packet on thread 0', 64) -> Discard;


avg :: HandlerAggregate( ELEMENT avg0 );

    magic[1]
    -> Unstrip(14)
    -> Print("WARNING: Unknown magic / untimestamped packet", -1)
    -> Discard;


}

receiveIN
-> Classifier(12/0800) -> MarkIPHeader(14) -> RIN :: Receiver($RAW_INsrcmac,"IN");

avgSIN :: HandlerAggregate( ELEMENT gen0/avgSIN);

dm :: DriverManager(  print "Waiting 2 seconds before launching generation...",
                print "EVENT GEN_STARTING",
                wait 2s,

                print "EVENT GEN_BEGIN",
                print "Starting gen...",
                print "Starting timer wait...",
                set starttime $(now),
                wait 10000000,
                set stoptime $(now),
                print "EVENT GEN_DONE",
                wait 1s,
                read receiveIN.hw_count,
                read receiveIN.count,
                read receiveIN.xstats,
                goto alatval $(eq 0 0),

                print "RESULT-LATENCY $(tsd.avg average)",
                print "RESULT-LAT00 $(tsd.avg min)",
                print "RESULT-LAT01 $(tsd.avg perc01)",
                print "RESULT-LAT50 $(tsd.avg median)",
                print "RESULT-LAT95 $(tsd.avg perc95)",
                print "RESULT-LAT99 $(tsd.avg perc99)",
                print "RESULT-LAT999 $(tsd.avg perc 99.9)",
                print "RESULT-LAT100 $(tsd.avg max)",
                goto alatval $(eq 0 0),
                set i 0,
                set step 1,
                label perc,
                print "CDFLATVAL-$(RIN/tsd.avg perc $i)-RESULT-CDFLATPC $(div $i 100.0)",
                set i $(add $i $step),
                set step $(if $(ge $i 99) 0.1 1),
                goto perc $(le $i 100.0),
                label alatval,
                print "RESULT-CLIENT-BUA $(bu.average)",
                print "RESULT-TESTTIME $(sub $stoptime $starttime)",
                print "RESULT-RCVTIME $(RIN/avg.avg time)",
                print "RESULT-THROUGHPUT $(RIN/avg.add link_rate)",
                set sent $(avgSIN.add count),
                set count $(RIN/avg.add count),
                set bytes $(RIN/avg.add byte_count),
                print "RESULT-COUNT $count",
                print "RESULT-BYTES $bytes",
                print "RESULT-SENT $sent",
                print "RESULT-DROPPED $(sub $sent $count)",
                print "RESULT-DROPPEDPC $(div $(sub $sent $count) $sent)",
                print "RESULT-TX $(avgSIN.add link_rate)",
                print "RESULT-TXPPS $(avgSIN.add rate)",
                print "RESULT-PPS $(RIN/avg.add rate)",
                print "BURST STATS $(bs.dump)",
                wait 2s,
                stop);

StaticThreadSched(dm 15);

