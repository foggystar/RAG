Starting answer generation...
STM32F103 系列微控制器有 5 种不同的封装，每种封装对应一套引脚配置（pinout）：

1. LFBGA100 – 10 × 10 mm 球栅阵列，100 引脚  
   图示见文档 Figure 3，页码 21。

2. LQFP100 – 14 × 14 mm 低轮廓四边扁平封装，100 引脚  
   图示见文档 Figure 4，页码 22。

3. UFBGA100 – 7 × 7 mm 极细间距球栅阵列，100 引脚  
   图示见文档 Figure 5，页码 23。

4. LQFP64 – 10 × 10 mm 低轮廓四边扁平封装，64 引脚  
   图示见文档 Figure 6，页码 24。

5. TFBGA64 – 8 × 8 mm 球栅阵列，64 引脚  
   图示见文档 Figure 7，页码 25。

6. LQFP48 / UFQFPN48 / VFQFPN36 等 48 引脚及 36 引脚小型封装  
   图示分别见文档 Figure 8（LQFP48，页码 26）、Figure 9（UFQFPN48，页码 26）及 Figure 10（VFQFPN36，页码 27）。

因此，STM32F103 系列微控制器的引脚配置（pinout）根据所选封装类型而定，共有上述 5 种（细分 8 个图示）。
Starting answer generation...
为了配置 STM32F103 不同封装（LFBGA100、LQFP100、UFBGA100、LQFP64、TFBGA64、LQFP48、UFQFPN48、VFQFPN36）的引脚为 GPIO、外设复用功能或模拟输入模式，需遵循以下步骤（参考引脚定义表“Table 5”及后续章节）：

1. **确认引脚封装与引脚号**  
   根据目标封装（如 LQFP48），在对应引脚图（如 Figure 8，页 25）中找到引脚编号（如 PA0、PB12 等）。

2. **查阅引脚功能表**  
   “Table 5”（页 28-32）列出的“Main function”（复位后默认功能）、“Default”（默认复用功能）和“Remap”（重映射功能）是关键。例如：
   - **PA0**：默认功能为 `PA0-WKUP`，复用为 `ADC12_IN0`、`TIM2_CH1_ETR`（页 28）。
   - **PB12**：默认功能为 `PB12`，复用为 `SPI2_NSS`、`TIM1_BKIN`（页 30-31）。

3. **配置为 GPIO**  
   - 在复位后，大多数引脚默认为 GPIO 模式（如 PA0、PB12）。需通过 `GPIOx_CRL`/`GPIOx_CRH` 寄存器设置方向（输入/输出）及模式（推挽/开漏、上拉/下拉）。例如：
     - 设置 PA0 为推挽输出：  
       `GPIOA->CRL &= ~(0xF << 0);`  
       `GPIOA->CRL |= (0x3 << 0);`  // 输出模式，50 MHz。

4. **启用外设复用功能**  
   - 若需使用复用功能（如 USART、SPI），需：
     1. 通过 `RCC_APB2ENR` 使能对应外设时钟（如 `RCC_APB2ENR_USART1EN`）。
     2. 在 `GPIOx_CRL`/`CRH` 中将引脚配置为“复用功能推挽/开漏”模式。例如：
        - 配置 PA9 为 USART1_TX：  
          `GPIOA->CRH &= ~(0xF << 4);`  
          `GPIOA->CRH |= (0xB << 4);`  // 复用功能推挽输出。

5. **模拟输入配置**  
   - 对于 ADC（如 PA0 的 `ADC12_IN0`），需：
     1. 在 `GPIOx_CRL` 中将引脚设为模拟模式（`0x0`）。
     2. 配置 ADC 通道（如 `ADC1->SQR3 |= (0 << 0);` 选择通道 0）。

6. **注意特殊限制**  
   - **PC13-PC15**：受限于电源开关，输出电流 ≤3 mA，速度 ≤2 MHz（页 33 注 5）。
   - **PD0/PD1**：需软件重映射（如在 LQFP48 中，需通过 `AFIO_MAPR` 设置 `SWJ_CFG` 位）。

**示例流程（以 LQFP48 的 PA0 为例）**：  
```c
// 1. 使能 GPIOA 时钟
RCC->APB2ENR |= RCC_APB2ENR_IOPAEN;

// 2. 配置 PA0 为模拟输入（ADC12_IN0）
GPIOA->CRL &= ~(0xF << 0); // 模拟模式

// 3. 配置 ADC
ADC1->CR2 |= ADC_CR2_ADON; // 使能 ADC
ADC1->SQR3 |= (0 << 0);    // 选择通道 0
```

通过以上步骤，可灵活配置 STM32F103 各引脚为所需模式。
Starting answer generation...
要在 STM32F103 上利用 I/O 引脚配置来启用具体外设（例如 USART、SPI 等），通常需要以下步骤。下面以 USART1 和 SPI1 为例，给出通用流程与对应的引脚映射（依据 Table 5，引脚定义位于 28/105–32/105 页）：

1. 选定外设工作引脚  
   • USART1：  
     TX → PA9（默认，可重映射到 PB6）  
     RX → PA10（默认，可重映射到 PB7）  
   • SPI1：  
     NSS → PA4（可重映射到 PA15）  
     SCK → PA5（可重映射到 PB3）  
     MISO → PA6（可重映射到 PB4）  
     MOSI → PA7（可重映射到 PB5）

2. 开启外设时钟  
   通过 RCC_APB2ENR（或 RCC_APB1ENR）寄存器中的相应位打开：  
   • USART1EN（位 14）  
   • SPI1EN（位 12）  
   • 需要时钟到 GPIO 端口（GPIOAEN 或 GPIOBEN）。

3. 配置引脚复用功能  
   使用 GPIOx_CRL 或 GPIOx_CRH 寄存器将对应管脚设为“复用推挽输出”或“浮空/上拉输入”：  
   • PA9 → USART1_TX：复用推挽输出，50 MHz  
   • PA10 → USART1_RX：浮空输入或上拉输入  
   • PA5/PA6/PA7 → SPI1 时钟/数据：按 SCK、MISO、MOSI 需求选择复用推挽或浮空输入。

4. 若需重映射，使能 AFIO 时钟并设置重映射位  
   • 打开 RCC_APB2ENR 的 AFIOEN（位 0）。  
   • 在 AFIO_MAPR 寄存器中将 USART1_REMAP 或 SPI1_REMAP 置 1。

5. 初始化外设寄存器  
   按参考手册对 USART_BRR、SPI_CR1 等寄存器设置波特率、数据位、时钟极性等参数。

6. 使能外设  
   置位 USART_CR1 的 UE 位或 SPI_CR1 的 SPE 位。

只要遵循上述步骤，即可完成 STM32F103 上任意指定外设的引脚配置与启用。
