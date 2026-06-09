# BabyAGI

> [!NOTE]
> The original BabyAGI from March 2023 introduced task planning as a method for developing autonomous agents. This project has been archived and moved to the [babyagi_archive](https://github.com/yoheinakajima/babyagi_archive) repo (September 2024 snapshot).

> [!CAUTION]
> This is a framework built by Yohei who has never held a job as a developer. The purpose of this repo is to share ideas and spark discussion and for experienced devs to play with. Not meant for production use. Use with caution.

---

This newest BabyAGI is an experimental framework for a self-building autonomous agent. Earlier efforts to expand BabyAGI have made it clear that the optimal way to build a general autonomous agent is to build the simplest thing that can build itself.

Check out [this introductory X/Twitter thread](https://x.com/yoheinakajima/status/1840678823681282228) for a simple overview.

The core is a new function framework (**functionz**) for storing, managing, and executing functions from a database. It offers a graph-based structure for tracking imports, dependent functions, and authentication secrets, with automatic loading and comprehensive logging capabilities. Additionally, it comes with a dashboard for managing functions, running updates, and viewing logs.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Function Metadata](#function-metadata)
- [Function Loading](#function-loading)
- [Key Dependencies](#key-dependencies)
- [Execution Environment](#execution-environment)
  - [Log](#log)
- [Dashboard](#dashboard)
- [Pre-loaded Functions](#pre-loaded-functions)
- [Future/Draft Features](#futuredraft-features)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

To quickly check out the dashboard and see how it works:

1. **Install BabyAGI:**

    ```bash
    pip install babyagi
    ```

2. **Import BabyAGI and load the dashboard:**

    ```python
from babyagi import agent
agent = agent.Agent()
response = agent.register()
print(response.text)
    ```