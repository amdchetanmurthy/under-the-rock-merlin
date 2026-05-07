# UnderTheRock - Dev Machine Setup (AWS)

## Overview

Development VMs are provisioned on AWS EC2 for UnderTheRock developers.

## Step 1: Launch EC2 Instance

1. Sign in to Okta: https://amdsso.okta.com/
2. Connect to AWS
3. Click on 'AdministrationAccess' under **AMD_AWS_AIG_Shark_DEV**
4. Region: **us-east-1** (top right)
5. Navigate: EC2 > Dashboard > Launch Instance

### Instance Configuration

| Setting | Value |
|---------|-------|
| Name | `Under-The-Rock-<UserName>` |
| OS | Ubuntu (Quick Start) |
| Instance Type | At least 8x vCPU, 64 GB RAM (e.g., `g4ad.4xlarge`) |
| Key Pair | Create new or reuse existing `.pem` key |
| VPC | `vpc-0bdcf0d0832a045ed` (shark-platform-aws-vpc) |
| Subnet | `shark-platform-aws--vpc-under-therock-subnet` |
| Security Group | `launch-wizard-13` (select existing) |
| Storage | At least 1x 2048 GiB gp3 Root volume |

### Connecting

```bash
ssh -i <path-to-key>.pem ubuntu@<private-ip>
```

**Note:** Must be connected to AMD internal network to reach the instance.

### Assigning to a Developer

SSH into the VM and add the developer's public SSH key to `~/.ssh/authorized_keys`.

## Step 2: Mount Directories via SSH (sshfs)

1. Create SSH key on the new VM:
   ```bash
   ssh-keygen
   ```

2. Install sshfs:
   ```bash
   sudo apt update && sudo apt install -y sshfs
   ```

3. Get public key:
   ```bash
   cat .ssh/id_ed25519.pub
   ```
   Add it to one of the gateway VMs (e.g., `taccuser@10.159.101.62`) in `~/.ssh/authorized_keys`.

4. Mount the directory:
   ```bash
   sudo sshfs -o IdentityFile=~/.ssh/id_ed25519 taccuser@10.214.116.183:/proj/verif_release_ro /proj/verif_release_ro
   ```

## Key Details

- AWS Account: AMD_AWS_AIG_Shark_DEV
- Region: us-east-1
- VPC: shark-platform-aws-vpc
- Subnet: shark-platform-aws--vpc-under-therock-subnet
- Gateway VM for NFS mounts: `taccuser@10.159.101.62` or `taccuser@10.214.116.183`
- Mount point: `/proj/verif_release_ro`
