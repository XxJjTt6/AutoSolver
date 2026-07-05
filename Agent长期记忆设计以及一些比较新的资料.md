**以下是与 Agent Harness 记忆系统（尤其是长期记忆沉淀、持久化存储、召回影响决策、Read/Write/Reflection 模式等）相关的参考资料及对应链接**（已按类别整理，仅提供资料和链接，无其他内容）：

### 主流 Agent 记忆框架（2026 年最常用）

- **Mem0**（最主流的独立记忆层，支持事实提取、合并、衰减、混合检索）  
  官网：https://mem0.ai/  
  文档：https://docs.mem0.ai/  
  论文：https://arxiv.org/html/2504.19413v1

- **Zep + Graphiti**（时序知识图谱，强在时间上下文和结构化事实沉淀）  
  官网：https://www.getzep.com/  
  Graphiti 相关：https://github.com/getzep/graphiti

- **Letta（原 MemGPT）**（OS 风格分层记忆，支持 Agent 自主管理长期记忆）  
  官网：https://letta.com/

- **LangMem + LangGraph Memory**（LangGraph 原生长时记忆，支持检查点 + 后台提取 + Memory Tools）  
  LangGraph 长时记忆相关：https://www.langchain.com/langgraph  
  相关课程：https://www.deeplearning.ai/courses/long-term-agentic-memory-with-langgraph

### Agent Harness 记忆架构相关资料

- **Martin Fowler - Harness engineering for coding agent users**  
  https://martinfowler.com/articles/harness-engineering.html

- **Addy Osmani - Agent Harness Engineering**  
  https://addyosmani.com/blog/agent-harness-engineering/

- **Addy Osmani - Loop Engineering**（记忆循环与 Harness 结合）  
  https://addyosmani.com/blog/loop-engineering/

- **LangChain - Improving Deep Agents with Harness Engineering**  
  https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering

- **LangChain - The Art of Loop Engineering**  
  https://www.langchain.com/blog/the-art-of-loop-engineering

### 2026 年记忆系统对比与调研

- **AI Agent Memory Systems in 2026: Mem0, Zep, Hindsight, Memvid 对比**  
  https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8

- **Best AI Agent Memory Systems in 2026: 8 Frameworks Compared**  
  https://vectorize.io/articles/best-ai-agent-memory-systems

- **AI Agent Memory 2026 — Comparing Mem0, Zep, Graphiti, Letta, LangMem**  
  https://medium.com/@wasowski.jarek/i-compared-5-ai-agent-memory-systems-across-6-dimensions-none-wins-6a658335ed0a

- **Survey of AI Agent Memory Frameworks 2026**  
  https://www.graphlit.com/blog/survey-of-ai-agent-memory-frameworks

- **Top Open-Source Memory Frameworks for LLM Agents in 2026**  
  https://www.cognee.ai/blog/guides/open-source-memory-frameworks-llm-agents

### Awesome Lists（资源合集）

- **awesome-harness-engineering**（Agent Harness 记忆相关工具与模式）  
  https://github.com/ai-boost/awesome-harness-engineering

- **Awesome-Agent-Harness**（含 110+ papers 的 Survey）  
  https://github.com/Gloriaameng/Awesome-Agent-Harness

- **awesome-agent-harness**（RUCAIBox 论文列表）  
  https://github.com/RUCAIBox/awesome-agent-harness

### 其他相关

- **Mem0 vs Zep 对比（生产级 Agent 记忆选择）**  
  https://mem0.ai/blog/mem0-vs-zep

- **Anthropic 相关 Harness 模式（长时运行 Agent 记忆设计参考）**  
  可通过搜索 “Anthropic effective harnesses long-running agents” 找到官方工程文章
