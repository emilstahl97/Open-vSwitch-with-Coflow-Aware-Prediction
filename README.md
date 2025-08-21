# Open-vSwitch-with-Coflow-Aware-Prediction

Software-defined Networking (SDN) has increasingly shifted towards hardware solutions that accelerate packet processing within data planes. However, optimizing the interaction between the data plane and the control plane, commonly referred to as the slow path, remains a significant challenge. This challenge arises because, in several major SDN applications, the control plane installs rules in the data plane reactively as new flows arrive, requiring time-consuming transitions to user space, which can become a significant bottleneck in high-throughput networks.

This thesis explores potential optimizations of Open vSwitch (OVS) by employing coflows to anticipate imminent network traffic, thus reducing the latency-inducing upcalls to the control plane, which are typically triggered by cache misses in the OVS megaflow cache. The study involves a series of benchmarks conducted on an OVN-simulated, single-node OCP cluster. These benchmarks utilize XDP to timestamp packets at both ingress and egress points of the cluster, measuring latency across various traffic scenarios. These scenarios are generated using synthetic coflow traffic traces, which vary in flow size distribution. The findings provide a comprehensive analysis of how OVS’s performance is influenced by accurately predicting varying proportions of future flows under different traffic conditions.

Results indicate that the benefits OVS gains from the ability to predict and preload flows are contingent upon the flow rate of the traffic trace. Notably, even a modest ability to foresee flows can result in enhancements in both maximum and mean latency, as well as reductions in CPU utilization. These improvements underscore the potential of predictive techniques in boosting data plane responsiveness and overall system efficiency. Suggestions for future work include developing a real-time coflow predictor that could dynamically load flows into the datapath during runtime. Such advancements could reduce latency and resource consumption in OVS production deployments.

#### Keywords: Open vSwitch, Software-Defined Networking, Slow path, Coflows

[ANRW 2025 Paper](https://dl.acm.org/doi/10.1145/3744200.3744762)

[Paper](paper/Enabling_traffic_prediction_in_virtual_switching_A_case_study.pdf)

[Thesis](thesis/Improving_Megaflow_Cache_Performance_in_Open_vSwitch_with_Coflow-Aware_Branch_Prediction.pdf)

[DiVA](https://urn.kb.se/resolve?urn=urn:nbn:se:kth:diva-361030)

[PDF at DiVA](https://kth.diva-portal.org/smash/get/diva2:1943521/FULLTEXT02.pdf)

[Presentation](https://youtu.be/ddpIN-swy2w?si=e8LfnuZkCXNVF3xA)

[Presentation OVSCON 2024](https://youtu.be/Z55xcDCCxgo?si=a4ksMEN8CLHtvgmL)

[Presentation OVSCON 2024 Q&A](https://youtu.be/hCVegvOWrqk?si=VuplRQ58GHBXitNZ&t=1421)
