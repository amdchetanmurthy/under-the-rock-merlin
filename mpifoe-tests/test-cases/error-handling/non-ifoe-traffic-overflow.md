---
topology: single-node
timeout: 180
pass_criteria: "Non-IFoE traffic manager handles RX buffer full, TX callback exhaustion, and inter-MID bounce failures gracefully"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Non-IFoE Traffic Manager Error Handling Test

## Purpose

Validates error handling in the non_ifoe_traffic manager (non_ifoe_traffic.c). Tests: (1) RX packet received when no host descriptor available (packet dropped silently), (2) TX callback registration when all slots full (returns EALREADY), (3) Inter-MID traffic bounce when MID1 is not available, (4) VLAN header parsing with unexpected ethertypes.

## Category

negative, error-handling

## Prerequisites

- MPIFoE firmware in SHOWTIME phase with non-IFoE traffic thread running
- Host traffic interface configured
- xncmdclient available

## Steps

1. **[host]** Verify non-IFoE traffic thread is running:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: SHOWTIME (non-IFoE traffic thread starts at DOWN->ETHERNET transition)

2. **[host]** Send L2 ping to verify basic non-IFoE RX path works:
   ```bash
   xncmdclient -c 'ifoe_l2_ping 0 64 1000; quit;'
   ```
   Expected: L2 ping responds

3. **[host]** Send traffic with no available RX descriptors:
   ```bash
   # Fill RX queue, then send additional packet
   # Packet should be consumed from hardware but not delivered to host
   ```
   Expected: No crash, packet silently dropped

4. **[host]** Attempt to register more TX callbacks than NUM_TX_CALLBACKS (1):
   ```bash
   # Second tx_register_packet_callback should return EALREADY
   ```
   Expected: Returns EALREADY

5. **[host]** Send non-IFoE packet to MID1-owned station from MID0:
   ```bash
   # send_non_ifoe_packet with netport_handle owned by remote MID
   # Should bounce via bounce_tx_to_mid1
   ```
   Expected: Packet delivered via inter-MID DMA

## Expected Result

- RX overflow handled gracefully (packet consumed from HW, dropped)
- TX callback overflow returns EALREADY
- Inter-MID bounce works when link is up
- VLAN-tagged and untagged packets parsed correctly
- Thread wake semaphore properly manages sleep/wake

## Failure Indicators

- Crash on RX overflow
- TX callback slot corruption
- Inter-MID DMA failure not handled
- VLAN parsing misidentifies ethertype
- Thread stuck in k_sem_take (deadlock)

## Cleanup

- None required
