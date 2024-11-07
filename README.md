# Improving-Megaflow-Cache-Performance-in-Open-vSwitch-OVS-with-Coflow-Aware-Branch-Prediction

The evolution of software-defined networking has increasingly favored hardware implementations for packet processing in data planes. Despite these advancements, optimizing the interaction between the data plane and the control plane, referred to as the slow path, remains a critical challenge. This interaction is poised to become a significant bottleneck in high-throughput networks.

This thesis explores potential optimizations of Open vSwitch (OVS) by employing coflows to anticipate imminent network traffic, thus reducing the latency-inducing upcalls to the control plane, which are typically triggered by cache misses in the OVS megaflow cache. The study involves a series of benchmarks conducted on an OVN-simulated, single-node OCP cluster. These benchmarks utilize XDP to timestamp packets at both ingress and egress points of the cluster, measuring latency across various traffic scenarios. These scenarios are generated using synthetic coflow traffic traces, which vary in flow size distribution. The findings provide a comprehensive analysis of how OVS's performance is influenced by accurately predicting varying proportions of future flows under different traffic conditions.

Results indicate that the benefits OVS gains from the ability to predict and preload flows are contingent upon the flow rate of the traffic trace. Notably, even a modest ability to foresee flows can result in enhancements in both maximum and mean latency, as well as reductions in CPU utilization. These improvements underscore the potential of predictive techniques in boosting data plane responsiveness and overall system efficiency. Suggestions for future work include developing a real-time coflow predictor that could dynamically load flows into the datapath during runtime. Such advancements could reduce latency and resource consumption in production deployments of OVS.

[Presentation](https://youtu.be/ddpIN-swy2w?si=e8LfnuZkCXNVF3xA)

[Presentation OVSCON 2024](https://youtu.be/Z55xcDCCxgo?si=a4ksMEN8CLHtvgmL)
