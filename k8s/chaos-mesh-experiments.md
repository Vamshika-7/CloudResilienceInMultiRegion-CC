# Chaos Mesh Network Fault Experiments

## 1. Objective
Evaluate how network degradation affects application resilience
using Chaos Mesh NetworkChaos experiments in Kubernetes.

## 2. Target Environment
- Kubernetes cluster: k3d-chaos-lab
- Namespace: chaos-lab
- Target pod label: run=network-test
- Experiment duration: 30 seconds
- Fault injection status: Not yet executed

## 3. Experiment Matrix

| Experiment | Action | Parameters | Duration |
|---|---|---|---|
| Network Delay | delay | Latency: 10ms, Jitter: 5ms | 30s |
| Network Jitter | delay | Latency: 10ms, Jitter: 20ms | 30s |
| Packet Loss | loss | Packet loss: 10%, Correlation: 0 | 30s |

## 4. Manifest Files
- network-delay.yaml
- network-jitter.yaml
- network-packet-loss.yaml

## 5. Pre-Execution Checks
1. Confirm the Kubernetes API is reachable.
2. Confirm Chaos Mesh components are healthy.
3. Confirm the chaos-lab namespace exists.
4. Confirm target pods have the label run=network-test.
5. Confirm the NetworkChaos resource is supported by the cluster.
6. Record the initial application health and baseline request results.

## 6. Execution Instructions
Run one experiment at a time, only after all pre-execution checks pass.

Check the current Kubernetes context:
kubectl config current-context

Check cluster nodes:
kubectl get nodes

Check Chaos Mesh pods:
kubectl get pods -n chaos-mesh

Inspect the target namespace and pods:
kubectl get pods -n chaos-lab --show-labels

Apply the selected experiment:
kubectl apply -f k8s/network-delay.yaml

Inspect the experiment:
kubectl get networkchaos -n chaos-lab
kubectl describe networkchaos test-network-delay -n chaos-lab

For the other experiments, use their corresponding manifest filenames.
Do not run multiple network faults simultaneously.

## 7. Cleanup
Delete the experiment that was applied:
kubectl delete -f k8s/network-delay.yaml

For jitter:
kubectl delete -f k8s/network-jitter.yaml

For packet loss:
kubectl delete -f k8s/network-packet-loss.yaml

Verify that no NetworkChaos experiments remain:
kubectl get networkchaos -n chaos-lab

## 8. Evidence to Collect
For every experiment, record:
- Experiment name and fault parameters
- Start and end timestamps
- Target workload and pod labels
- Baseline application response time and error rate
- Application response time and errors during the fault
- Chaos Mesh experiment status and relevant logs
- Recovery time after fault removal
- Evidence that the experiment was removed
- Any installation, permission, or connectivity errors

## 9. Results Log

| Experiment | Baseline | During Fault | Recovery | Status |
|---|---|---|---|---|
| Network Delay | Pending | Pending | Pending | Not executed |
| Network Jitter | Pending | Pending | Pending | Not executed |
| Packet Loss | Pending | Pending | Pending | Not executed |

## 10. Current Limitation
The Kubernetes API previously timed out during setup.
Experiments must remain unexecuted until the API is reachable,
Chaos Mesh is healthy, and the target workloads are verified.
No fault-injection or recovery results are claimed at this stage.
