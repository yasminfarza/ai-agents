#!/usr/bin/env python
import os
from financial_researcher.crew import ResearchCrew

os.makedirs('output', exist_ok=True)

def run():
    """
    Run the crew.
    """
    inputs = {
        'company': 'Apple'
    }
    
    result = ResearchCrew().crew().kickoff(inputs=inputs)
    
    print("\n\n=== Final Output ===\n\n")
    print(result.raw)
    
    print("\n\nReport has been saved to output/report.md")
    
if __name__ == "__main__":
    run()
    