# hackthefork-mas

This code was created during the hackathon [Hack the Fork](https://www.hackthefork.com/) taking place the 13th and 14th of December 2025 in Paris, promoting AI based innovation in FoodTech.

Our team proposed a solution to replace animal based products in recipes such as eggs for foam and emulsion, taking into account available tools, budget and other production constraints using precision fermentation thanks to a multi-agent system using the google ADK framework.
To see how it works, see the [documentation](https://google.github.io/adk-docs/get-started/python/).

This repo hence contains the files for a multi-agent system, with an orchestrator with which we communicate, and sub agents called by the orchestrator to be the experts in various domains of the analysis, i.e. an integration agent for technical analysis, an economics agent for financial analysis, a regulatory agent for regulatory check, a quality agent for quality check and a risk agent for risk assessment. The orchestrator gives a final summary and a final decision on feasibility. The sub agents use `gemini-2.0-flash-exp` and the orchestrator `gemini-3-pro-preview`.

Please note that all this has been done over a weekend, among a lot of other things, so it is not refined and should be experimented upon for better results.
