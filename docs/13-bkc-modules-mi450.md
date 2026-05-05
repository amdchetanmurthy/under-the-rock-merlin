# BKC Modules - MI450 (Datacenter GPU)

## Overview

The BKC Modules spreadsheet tracks all firmware, driver, software, and tool components that comprise the MI450 BKC. The spreadsheet has 6 sheets: Client, Navi3x, SCBU, Graphics, Datacenter GPU - MI350, Datacenter GPU - MI450. The MI450 sheet is the primary UnderTheRock target with 176 rows.

## MI450 Column Headers

Binary name | Category | Module/Package | BKC Component | Customer Specific?? | Description | Build Engineer Contact | Owner | VP | Owner org | Source location | Workflow/Location of Build Script | Build Deps | Consumption Model | Follow up required | Frequency of promotion | Pre-si Coverity/lint | Pre-si Simnow | Post-si smoke | CI/CD Priority | ROCm CI/CD exists? | Delay to test with nightly ROCm? | ETA for CI/CD w/ROCm | Location of build output | Release location | License type

## EAM BKC — Firmware (IFWI) Components

| Binary ID | Name | Description | Build Engineer | Owner |
|-----------|------|-------------|----------------|-------|
| 0x0001 | MPASP_FMC | FMC (First Mutable Code) | WilliamC, NG/Zachary Sun | - |
| 0x0002 | TEE Trusted OS | Trusted Execution Env, Trusted OS | Khaymov, Mikhael, Jamin | - |
| 0x0008 | PMFW MID MP1 | Power management firmware MP1 on MID | Matt Mione, Alex Cheung | Ke Deng |
| 0x0009 | Secure Policy RSMU Init | Secure policy configuration | Anas Siraj | Nezami, Md Tarique |
| 0x0015 | TEE Key Manager Driver | Trusted Execution key manager driver | Jarvis Wang/Ivo | Ting-Yu Lin |
| 0x001b | TEE Boot Driver | Boot driver for trusted env | Jarvis Wang/Ivo | Ting-Yu Lin |
| 0x001c | TEE SoC Driver | Trusted env system on chip driver | Jarvis Wang/Ivo | Ting-Yu Lin |
| 0x001d | TEE HAD Driver | AMDTEE Driver: Main TEE driver for Linux | Jarvis Wang/Ivo | Ting-Yu Lin |
| 0x001f | TEE Interface Driver | TEE Interface Driver | Jarvis Wang/Ivo | Ting-Yu Lin |
| 0x0020 | IP Discovery Binary | Discovery Binary | Eric Lu | Terry Ng |
| 0x0024 | Security Policy L0 | Security Policy | Anas Siraj | Nezami, Md Tarique |
| 0x0028 | TEE System Driver | TEE System Driver | Srinidhi Vijayendra | Ting-Yu Lin |
| 0x0045 | Security Policy TOS Late | Security Policy for Trusted OS | Anas Siraj | Nezami, Md Tarique |
| 0x004f | UMC FW | Unified Memory Controller FW | Jin Chung Teng | Justin Zhou1 |
| 0x0050 | ASP BL Key Database | ASP Bootloader Key Database | Valeri Kirischian | Ting-Yu Lin |
| 0x0055 | ASP Anti Rollback | Anti rollback table | Fatema Hazari | Ting-Yu Lin |
| 0x005c | SPIROM Info | SPIROM Information Config | Fatema Hazari | Ting-Yu Lin |
| 0x005d | MPIO FW | Multi-Purpose I/O component | Matheus Gomes | Carlos Velasco |
| 0x0064 | TEE RAS Driver | Trusted OS RAS driver | Vikram Travedi | Ting-Yu Lin |
| 0x0065 | ASP RAS TA | RAS trusted apps | John Matthews | Ting-Yu Lin |
| 0x0068 | TEE SPDM Driver | - | Kieran Simm | Ting-Yu Lin |
| 0x0069 | TEE DPE Driver | - | Kieran Simm | Ting-Yu Lin |
| 0x006a | TEE Pre-eSID Driver | - | Vikram Tivedi | Ting-Yu Lin |
| 0x006b | MPRAS FW | - | John Matthews | Ting-Yu Lin |
| 0x006c | TEE Post-eSID Driver | - | Vikram Tivedi | Ting-Yu Lin |
| 0x0076 | DF RIB | Data created from PPR XML | Krishna Bernucho | - |
| 0x009b | IMU FW | - | Matt Mione, Alex Cheung | Ke Deng |
| 0x009c | IMU Data | - | Matt Mione, Alex Cheung | Ke Deng |
| 0x009d | ART LibROM Overlay | LibROM Overlay patch for ART | Andrew Hocking | Ting-Yu Lin |
| 0x009f | Register Access Whitelist | - | Keiran Simm | Ting-Yu Lin |
| 0x00a8 | Caliptra | Caliptra Root of Trust Firmware | Nicholas Quarton | John Traver |
| 0x00ab | MPART FMC | - | Andy Chik | Ting-Yu Lin |
| 0x00ac | MPART Runtime FW | - | Andy Chik | Ting-Yu Lin |
| 0x00ad | MPART Key Database | - | Andy Chik | Ting-Yu Lin |
| 0x00ae | ASP LibROM Overlay | LibROM Overlay patch for ASP | Andrew Hocking | Ting-Yu Lin |
| 0x00b5 | CLD Firmware | - | Brian Sieu | Keith Shaw |
| 0x0101 | Secure Policy L1 | - | Anas Siraj | Nezami, Md Tarique |
| 0x0135 | MPRAS Applet 2 | - | John Matthews | Ting-Yu Lin |
| 0x0147 | Memory Init Config Table | - | Sai Kammila | Ricardo Quintana/Pushkin S |
| 0x0156 | ROM_STRAP | - | Queena Zhou | Fransciso Toro |
| 0x0157 | eSID TOC | - | Mathias Rosas | Fransciso Toro |
| 0x0158-015c | eSID 0-4 | - | Mathias Rosas | Fransciso Toro |
| 0x01e0 | MPNHT FW | - | Alex Jivin | Ting-Yu Lin |
| 0x01ea | PMFW AID MP5 | PM firmware Micro Processor 5 on AID | Matt Mione, Alex Cheung | Ke Deng |
| 0x01ec | UCIe PHY FW | - | Johnson Tsai | Keith Shaw |
| 0x01f3 | MPIFoE FW | Infinity Fabric over Ethernet | Chris Key | Laurence Evans |
| 0x01f7 | TEE SRIOV Driver | - | Zhaochen Zhang | Ting-Yu Lin |
| 0x01f9 | GTA PHY | - | Ed C. Lee | Ed C. Lee |
| 0x01fa | IFOE PHY | Infinite Fabric over Ethernet PHY | Ed C. Lee | Ed C. Lee |
| 0x01fb | VBL Runtime Driver | VBL Runtime Driver | Marco Herdia | Fransciso Toro |
| 0x1051 | PMFW XCD MP5 | PM firmware Micro Processor 5 on XCD | Matt Mione, Alex Cheung | Ke Deng |
| 0x1053 | APCB_DEFAULT_RECOVERY | AGESA PSP Control Block | Mathias Rosas | Fransciso Toro |
| 0x1054 | APCB_UPDATABLE | AGESA PSP Control Block | Abir Hossain | Robert Szurtei |
| 0x1055-1057 | APCB Backup/Eventlog | AGESA PSP Control Block variants | Marco Herdia | Fransciso Toro |
| 0x0021 | Pre-Si IKEK | Binary for token/signature | Vincent Ngo | Ting-Yu Lin |
| 0x01C4 | Soft Fuse | Soft Fuse configuration | Valeri Kirischian | Ting-Yu Lin |

## EAM BKC — Firmware (Part of Driver)

| Name | Description | Build Engineer | Owner |
|------|-------------|----------------|-------|
| lsdma | Lightweight System DMA controller | - | SW GFX |
| MES | Micro engine scheduler firmware | Alvin Huan | Alvin Huan |
| CP | Command Processor | Edwin Lau | Fransciso Toro |
| RLC | RunList Controller (splitting into RLCG & RLCV) | Brad Johnson | Fransciso Toro |
| sdma | System DMA engine | Alvin Huan | Alvin Huan |
| VCN FW | VCN Firmware | Alvin Huan | Alvin Huan |

## EAM BKC — Software Drivers

| Name | Description | Build Engineer | Owner |
|------|-------------|----------------|-------|
| IFoE driver | Linux GPU KMD - IFoE host driver on x86 | Pieter Jansen Van Vuuren | - |
| AMDGPU | Linux GPU kernel mode driver | Le Ma/Hawking Zhang | Jeff Weyman |
| AMD GPU FIRMWARE | GPU firmware loaded by GPU driver | Le Ma/Hawking Zhang | Jeff Weyman |
| GIM | Linux SRIOV Host Driver | Amar Patel | Mario Filipes |
| SRIOV Guest Driver | Linux SRIOV Guest Driver | Amar Patel | Mario Filipes |

## EAM BKC — Platform Firmware

| Name | Description | Build Engineer | Owner |
|------|-------------|----------------|-------|
| AMC FW | Accelerator Management Controller | Joseph Chua | Xavier Carbo |
| AMC ERoT FW | External Root of Trust device | Joseph Chua | Xavier Carbo |
| AMC FPGA FW | AMC FPGA Firmware | john.feikis/mohammad.imran | John Feikis/Samir Gundawar |
| EAM FPGA FW | Engine Accelerator Module FPGA | john.feikis/mohammad.imran | John Feikis/Samir Gundawar |
| EAM Board Power VR FW | Power Configuration VR config | Thurein.paing/mohammad.imran | Thurein Paing/Imran Mohammad |

## AINIC BKC Components

| Name | Description | Build Engineer | Owner |
|------|-------------|----------------|-------|
| Velsei UALoE Driver | OCI NIC | Vijay Gopinath | Martin |
| Velsei NIC FW Bundle | Drivers, FW for SuC/SOC/FPGA, Host Tools | Vijay Gopinath | Martin |
| Saraceno/Mortaro NIC FW Bundle | AINIC Bundle | Vijay Gopinath | Martin |
| Leni NIC FW Bundle | AINIC Bundle | Vijay Gopinath | Martin |

## AIFM BKC Components

| Name | Description | Build Engineer | Owner |
|------|-------------|----------------|-------|
| Switch NOS | Switch Network OS | Vijay Srinivasan | Vijay Srinivasan |
| AFM Controller | Instinct Fabric Manager Controller | Enrico | Enrico |
| AFM Agent | Instinct Fabric Manager Agent | Enrico | Enrico |

## Rack BKC Components

| Name | Description | Build Engineer | Owner |
|------|-------------|----------------|-------|
| Power Shelf PMC ERoT FW | PMC ERoT | Saakyan, Artem/Dunn Jamie | Samir Gundawar |
| Power Shelf PMC FW | PMC Firmware | Saakyan, Artem/Dunn Jamie | Samir Gundawar |
| Power Shelf PSU FW | PSU Firmware | Saakyan, Artem/Dunn Jamie | Samir Gundawar |
| Instinct Rack Manager SW | Remote Management | Matthew Stern | Tim Arn |
| AMD Rack Check | Rack-level diagnostic framework | Emad Haque | Tim Arn |
| AMD Node Check | GPU/CPU/AINIC health checks | Jason Albert | Sirish C. |

## EAM BKC Tools

| Name | Description |
|------|-------------|
| AFMCTL | CLI tool to manage/monitor IFoE in GPU |
| AMDXIO | PCIe 2D Margin, Link health, XGMI, IFoE, UCIe, UAlink monitoring |
| AGT | Voltage, Clock, PM logging, FW loading, Device details |
| AMD GPU RAS Tool | HBM ECC, NBIO Parity, MPIO, xGMI, PCIe, VCN error injection/query |
| ADDC | Cover GPU, CPU, AINIC diagnostics |

## HPM BKC Components

| Name | Build Engineer |
|------|----------------|
| Venice AGESA (EDK2.0 SBIOS) | Sunglin Lu |
| HPM CPLD LCMXO5 (EVT1/EVT2) | Scott Hsieh |
| BB CPLD LCMXO5 (EVT1/EVT2) | Scott Hsieh |
| AMI SBIOS (Meta) | Raj Natarajan |

## ROCm Stage 1 Components (Build Engineer: Chris Sosa)

rock-dkms, rocm-clang-ocl, atmi, kfdtest, llvm-amdgpu, comgr, rocm-device-libs, hipcc, hip-runtime-amd, rocm-dkms/utils/libs/dev, rocm-opencl, rocm_smi_lib64, hsa-rocr-dev, hsakmt-roct, rocm-cmake, rocminfo, roctracer, rocprofiler, hsa-amd-aqlprofile, rocm-gdb, rocm-dbgapi, rocr-debug-agent, rocm-bandwidth-test, hipify-clang, rdc, amdgpuras, aomp-amdgpu

## ROCm Stage 2 Components (Build Engineer: Chris Sosa)

rocblas, hipblas, Tensile, rocFFT, hipFFT, rocRAND, rocPRIM, rocSPARSE, hipSPARSE, rocHPCG, MIGraphX, rocALUTION, mivisionx, RPP, rocAL, rocDecode, rocThrust, half, MIOpen, MIOpenKernels, TUNA, hipCUB, rocSOLVER, hipSOLVER, rocm-validation-suite, rccl, ucx, Open MPI, rocWMMA, hipTensor, composable_kernel, hipBLASLt, hipFORT, hipSPARSELt, rocGRAPH

## Frameworks (Build Engineer: Chris Sosa)

TensorFlow, PyTorch, ONNX-RT

## Other Sheets in the Spreadsheet

| Sheet | Rows | Description |
|-------|------|-------------|
| Client | 159 | Client/desktop GPU driver components (SW GFX org) |
| Navi3x | 126 | Navi3x-specific BIOS/firmware components |
| SCBU | 126 | Semi-Custom BU components |
| Graphics | 119 | Graphics subsystem components |
| Datacenter GPU - MI350 | 138 | MI350 BKC components (similar structure to MI450) |
| Datacenter GPU - MI450 | 176 | MI450 BKC components (primary UnderTheRock target) |
