# AI Investor

**Description:** The AI investor will be an agent investor powered by AI and MCPs. It will gather stock information from eodhd, read my current holdings in Nordnet, and use this information to maintain my entire investment portfolio in what it determines is the best possible way based on the strategy given.

## Investment strategy:
- Minimise risk and think long-term. 
- All stocks should be positive or close to it. No large price rises or falls due to taking too much risk.
- Prioritise dividends and large companies (monopolies or close to it) with a potential for high upside in the long-term.
- Use fundamental analysis to determine investments.

## Teck-stack
- Python
- Claude Agent SDK

## Description of functionality
- From a shortlist of potential stocks, gather information from EODHD about each of them.
- Analyse each company. Based on certain necessary criterions, filter out most of them. No overvalued companies should be considered.
- Consider current holdings as well as the available funds in Nordnet.
- Based on the information above, determine which positions should be held/increased/decreased/sold completely, and which stocks not already invested in should be bought, and how much.
- Provide a detailed report of considerations, thought processes, decisions, etc. that will be sent to my email "patrick.alfei.sabo@gmail.com"

## Documentation
- Provide a well structured and formulated documentation of the implementation and functionality of the project in a "docs" directory. The language should be concise and structured. Use bullet points, code blocks, etc.

## Environment and considerations
- Ensure the optimal setup of this project
- Use good python conventions when coding
- In order to use up-to-date documentation when programming, use context7
