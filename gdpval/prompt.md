Create a single-page web app with a beautiful New York Times style data visualization showing the impact of AI across sectors and occupations based on OpenAI's GDPVal paper: https://openai.com/index/gdpval/

The aim is to help the audience understand which large sectors have the highest potential for AI task augmentation.

Draw a nested D3 treemap like https://observablehq.com/@d3/nested-treemap but with a wide aspect ratio of 2:1.
Ensure a responsive design. Use full screen width.

The hierarchy is Sector > Occupation, with size based on "Compensation" from compensation.csv.

The color is a diverging scale based on max(Win) across models from win.csv. 0% = red, 50% = yellow, 100% = green.

The Sector labels should show just the sector name.
The Occupation labels should render the occupation name. Additionally, show the compensation as $x.xxB at the bottom.

Hovering over any Occupation should show a tooltip like this:

- Sector: Real Estate and Rental and Leasing
- Occupation: Concierges
- Compensation: $1.80B
- Model Win Rate: 29% (Claude)

Clicking on any Occupation should open a modal dialog that shows a collapsible list of the prompts from prompts.csv. There are multiple prompts per occupation. Show all. Prompts are long. Allow scrolling in the modal. Esc should close the modal.

Columns:

- compensation.csv: Sector,Occupation,Compensation
- prompts.csv: Sector,Occupation,Prompt
- win.csv: Sector,Occupation,Model,Win

Document the steps you took and errors faced in process.md
