![discountAssistant](https://socialify.git.ci/zuo-shi-yun/discountAssistant/image?description=1&logo=https%3A%2F%2Fi.postimg.cc%2FDy2Qft7h%2F20.png&name=1&theme=Light)
加了淘宝京东的羊毛群但是懒得天天看？<br/>
错过了神车而懊恼不已？<br/>
想淘一点不急着用的东西？<br/>
优惠卷小助手帮你解决上面所有问题！<br/>
安装我，添加监听群、关键字，踏上愉快的薅羊毛之旅吧！<br/>
(本插件运行于[QChatGPT](https://github.com/RockChinQ/QChatGPT))
<details>
<summary> 

## :muscle:插件功能

</summary>

<details><summary>从监听群中自动筛选含有关键字的优惠券</summary>

- 自动检测监听群的信息，将含有关键字的信息发送给查询该关键字的好友、QQ群

</details>

<details>
<summary>优惠券去重</summary>

- 使用[text2vec-base-chinese](https://huggingface.co/shibing624/text2vec-base-chinese)模型对优惠券信息去重，避免信息重复

</details>

<details>
<summary>多步骤信息处理机制</summary>

- 多步骤信息：有的信息需要凑单，故可能有很多步操作，有多条信息
- 本系统自动识别含有关键字的多步骤信息，并将多步骤信息的后续信息一并发送

</details>

<details>
<summary>可疑信息处理机制</summary>

- 可疑信息：有的信息，诸如美团饿了么红包，是以二维码形式发送的，一般这样的操作复杂不止一条信息。
- 本系统自动识别这类不含优惠码的可疑信息，并可根据配置自动发送可疑信息的相关信息

</details>

<details>
<summary>多种策略的关键字检测机制</summary>

- 关键字检测支持正则且忽略大小写
- 支持通过指令快捷生成多种规则的关键字

</details>

<details>
<summary>灵活完善的系统设计</summary>

- 允许以非“!cmd”的形式与本系统进行交互
- 系统保留一定时间的优惠券信息、全部监听群信息，便于优惠券查询
- 可根据配置自动清理数据库，保证系统运行速度

</details>

</details>

<details>
<summary>

## :crossed_swords:安装与配置

</summary>
<details>
<summary>安装</summary>

- 运行`!plugin get https://github.com/zuo-shi-yun/discountAssistant.git`
    - 因本插件需下载模型，请耐心等待，如果系统长时间未出现**下载进度条**，请重新启动系统。
    - 下载该模型需科学上网，如安装时间过长/无法安装，请从该
      [官方链接](https://huggingface.co/shibing624/text2vec-base-chinese/tree/main)
      或[网盘链接](https://pan.baidu.com/s/15Y4ptxTKAS8Ia5X7Y7QAaQ?pwd=3r4n)(无需科学上网，密码：3r4n)
      下载pytorch_model.bin文件并放入plugins/discountAssistant/model目录下。
- 进入插件目录执行`pip install -r requirements.txt`

</details>
<details>
<summary>配置</summary>

- 系统相关配置存于config.py文件中，每一项配置均有详细说明。
- 可对插件运行逻辑、数据库清理、优惠券信息处理流程进行配置。
- 该配置不支持动态加载，修改后请**重启系统**

</details>

</details>

<details>
<summary>

## :calling:交互指令

</summary>

### 说明

- 下面的所有指令(cmd)均有两种形式，“**!cmd**”以及“**cmd**”。  
  其中“**cmd**”形式的指令只有当config文件中normal_cmd字段为True时有效（默认为True）。  
  下文中“**!**”省略不写，若使用“!cmd”形式时别忘了加。
- 下面的所有命令均对**好友以及群聊**有效。  
  若在qq群以“**@机器人 cmd**”形式与系统交互，视作为该群调整配置，检测到的信息将发送到qq群中。  
  反之在私聊里以“**cmd**”形式则是与用户交互，视作为用户调整配置，检测到的信息也将私聊发给用户。
- 可以向机器人发送"**优惠**"快速查看指令说明

<details>
<summary>

### 筛选关键字

</summary>

1. **添加优惠券关键字**："添加关键字 要添加的关键字"。  
   eg：筛选关于卫生纸的优惠券：添加关键字 卫生纸  
   关键字忽略大小写且支持正则。
2. **一次性添加多个关键字**："添加关键字 要添加的关键字1 要添加的关键字2"。  
   eg：一次性添加含有麦当劳、含有肯德基的关键字：添加关键字 麦当劳 肯德基  
   关键字无数量限制。
3. **筛选某一关键字时不包含其他关键字**："添加关键字 要添加的关键字 不包含 不希望包含的关键字1 不希望包含的关键字2"  
   eg：筛选包含"猫"但不包含"天猫"、"猫超"的优惠券：添加关键字 猫 不包含 天猫 猫超  
   无数量限制。  
   tips：比如我想筛选固态，结果系统把固态白酒也筛选到了，这时可以使用该指令检测包含"固态"不包含"白酒"的优惠卷
4. **筛选同时含有多个关键字的优惠券**："添加关键字 要添加的关键字 同时包含 同时包含的关键字1 同时包含的关键字2"  
   eg：筛选同时含有抖音、卫生纸的关键字：添加关键字 抖音 同时包含 卫生纸  
   无数量限制。  
   tips：比如我想筛选硬盘，但是我只希望要容量大的硬盘，这时可以使用该指令检测同时包含“硬盘”和“T”的优惠券。
5. **查询所有检测的关键字**："查询关键字"
6. **删除关键字**："删除关键字 要删除的关键字"
7. **通过关键字序号删除关键字**："删除关键字 要删除的关键字序号"  
   关键字序号可以通过"查询关键字"指令获得。  
   tips：该功能旨在简化当关键字过于复杂时的删除操作。

</details>

<details>
<summary>

### 监听群

</summary>

1. **添加优惠券监听群**："添加群 群qq号"。  
   eg：在群号为12345的群中筛选优惠券：添加群 12345
2. **删除监听群**："删除群 群qq号"

</details>

<details>
<summary>

### 查询优惠券

</summary>

1. **查询某条信息的相关信息**："查询相关信息 要查询信息的ID 查询条数"。  
   tips：有的信息，诸如美团饿了么红包，是以二维码形式发送的，  
   一般这样的操作复杂不止一条信息，而系统只会自动发送一条信息。  
   该功能旨在应对这种情况。
2. **查询优惠券原信息**："查询原信息 要查询信息的ID"  
   ID指优惠券信息最下方的ID。  
   tips：该功能旨在应对消息不完整或代码无法识别的情况。
3. **在所有监听群内查询含有关键字的信息**："查询所有信息 关键字"。  
   tips：比如我突然想找麦当劳的优惠券，但是我之前并没有筛选麦当劳，此时可以使用该功能从所有信息中筛选优惠券。  
   因信息量可能过大导致模型运行时间过长，故该指令不具备去重功能
4. **查询含有指定关键字的优惠券信息**："查询优惠券 关键字"  
   eg：查询含有电热毯的优惠券：查询优惠券 电热毯  
   tips：优惠卷、优惠券、优惠劵都可以。用于当用户关闭主动发送时查询优惠券。

</details>

<details>
<summary>

### 主动发送优惠券

</summary>

1. **打开优惠卷信息实时发送**(默认实时发送)："打开发送"。
2. **关闭优惠券信息实时发送**："关闭发送"。

</details>

<details>
<summary>

### 主动清理数据库

</summary>

该指令仅管理员可用

1. **根据默认时间范围清理数据库**："清理数据库"。
2. **根据指定时间范围清理数据库**："清理数据库 优惠券信息时间范围 全部监听群信息时间范围"。  
   eg：保留一天内的优惠券信息、保留两天内的全部监听群信息："清理数据库 1 2"。  
   为0时清理全部信息

</details>

</details>