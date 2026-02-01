"""Ultralong context demo: 100+ tool calls that would kill normal context windows.

This demonstrates RLM's ability to handle contexts 2 orders of magnitude
beyond model limits through programmatic examination.
"""

# Ensure Weave is initialized (imports agent which imports weave_init)
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.agent import run_agent
from rvla.memory import workspace_from_env
from rvla.web import WebDriver
from rvla.multi_agent_coordinator import MultiAgentCoordinator


def research_and_compare_saas_pricing():
    """Research 10+ SaaS products, compare pricing, extract features.
    
    This task requires:
    - 10+ websites to visit
    - 50+ page navigations
    - 100+ observations/actions
    - Long context (all research data)
    - RLM to examine context programmatically
    """
    
    goal = """Research and compare SaaS pricing across multiple categories:
    
    1. Project Management Tools (3-4 tools)
    2. CRM Software (3-4 tools)
    3. Email Marketing (2-3 tools)
    
    For each tool:
    - Navigate to pricing page
    - Extract pricing tiers and features
    - Note any special offers or discounts
    - Compare value propositions
    
    Then:
    - Create comparison table
    - Identify best value in each category
    - Generate summary report
    
    This will require 100+ tool calls and create a massive context.
    RLM will examine this context programmatically instead of loading it all."""
    
    workspace = workspace_from_env()
    driver = WebDriver()
    coordinator = MultiAgentCoordinator()
    
    print("="*70)
    print("ULTRALONG CONTEXT DEMO: SaaS Pricing Research")
    print("="*70)
    print(f"\nGoal: {goal}\n")
    print("[INFO] This will generate 100+ tool calls")
    print("[INFO] RLM will examine context programmatically\n")
    print("="*70 + "\n")
    
    result = run_agent(
        goal=goal,
        driver=driver,
        workspace=workspace,
        enable_multi_agent=True,
    )
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Total steps: {len(result['trajectory'])}")
    print(f"Total events: {len(result['events'])}")
    print(f"Context size: ~{sum(len(e) for e in result['events'])} characters")
    print(f"\nScore: {result['score']}")
    
    # Show RLM examination events
    rlm_events = [e for e in result['events'] if 'rlm_examination' in e]
    print(f"\nRLM examinations: {len(rlm_events)}")
    if rlm_events:
        print("RLM successfully examined context programmatically!")
        print(f"Last examination: {rlm_events[-1][:100]}...")
    
    return result


def multi_site_job_search():
    """Search for jobs across multiple job boards with complex filters.
    
    This creates ultralong context through:
    - Multiple job board sites (LinkedIn, Indeed, Glassdoor, etc.)
    - Complex filtering and searching
    - Extracting job details
    - Comparing opportunities
    - 100+ tool calls
    """
    
    goal = """Search for software engineering jobs across multiple platforms:
    
    1. LinkedIn Jobs
    2. Indeed
    3. Glassdoor
    4. AngelList (for startups)
    
    For each platform:
    - Search with filters (location, salary, remote, etc.)
    - Navigate through search results (multiple pages)
    - Extract job details (title, company, salary, requirements)
    - Note application deadlines
    
    Then:
    - Compare opportunities
    - Identify best matches
    - Create organized list
    
    This requires navigating 20+ pages and extracting 50+ job listings.
    Context will be massive - RLM handles it programmatically."""
    
    workspace = workspace_from_env()
    driver = WebDriver()
    
    print("="*70)
    print("ULTRALONG CONTEXT DEMO: Multi-Site Job Search")
    print("="*70)
    print(f"\nGoal: {goal}\n")
    print("[INFO] Will navigate 20+ pages, extract 50+ jobs")
    print("[INFO] Creates massive context - RLM examines programmatically\n")
    
    result = run_agent(
        goal=goal,
        driver=driver,
        workspace=workspace,
        enable_multi_agent=True,
    )
    
    return result


def comprehensive_product_research():
    """Research a product category across many sites and sources.
    
    Creates ultralong context through:
    - Multiple review sites
    - Comparison sites
    - Manufacturer sites
    - Forum discussions
    - 100+ tool calls
    """
    
    goal = """Research 'Best Laptops for Software Development 2026':
    
    1. Review Sites (5-6 sites: Wirecutter, TechRadar, etc.)
    2. Comparison Sites (3-4 sites)
    3. Manufacturer Sites (Apple, Dell, Lenovo, etc.)
    4. Reddit/Forum Discussions (2-3 threads)
    
    For each source:
    - Navigate to relevant pages
    - Extract recommendations and ratings
    - Note pros/cons
    - Capture pricing information
    
    Then:
    - Cross-reference findings
    - Identify consensus top picks
    - Create comprehensive comparison
    - Generate buying guide
    
    This requires 100+ tool calls across 15+ websites.
    Context will be enormous - perfect RLM test case."""
    
    workspace = workspace_from_env()
    driver = WebDriver()
    
    print("="*70)
    print("ULTRALONG CONTEXT DEMO: Comprehensive Product Research")
    print("="*70)
    print(f"\nGoal: {goal}\n")
    print("[INFO] 100+ tool calls across 15+ websites")
    print("[INFO] Massive context - RLM handles it\n")
    
    result = run_agent(
        goal=goal,
        driver=driver,
        workspace=workspace,
        enable_multi_agent=True,
    )
    
    return result


def complex_multi_step_form_completion():
    """Complete a complex multi-page form with dependencies.
    
    Creates ultralong context through:
    - Multiple form pages (10+)
    - Conditional logic
    - Data validation
    - Error handling and retries
    - 100+ tool calls
    """
    
    goal = """Complete a complex application form across multiple pages:
    
    The form has:
    - Personal information (page 1)
    - Education history (page 2-3, multiple entries)
    - Work experience (page 4-6, multiple entries)
    - References (page 7-8, multiple entries)
    - Documents upload (page 9)
    - Review and submit (page 10)
    
    Requirements:
    - Navigate between pages
    - Fill forms with correct data
    - Handle conditional fields
    - Validate inputs
    - Handle errors and retries
    - Upload documents
    - Review before submission
    
    This creates 100+ tool calls with complex state management.
    RLM examines context programmatically to track progress."""
    
    workspace = workspace_from_env()
    driver = WebDriver()
    
    print("="*70)
    print("ULTRALONG CONTEXT DEMO: Complex Multi-Page Form")
    print("="*70)
    print(f"\nGoal: {goal}\n")
    print("[INFO] 10+ form pages, 100+ tool calls")
    print("[INFO] Complex state - RLM manages context\n")
    
    result = run_agent(
        goal=goal,
        driver=driver,
        workspace=workspace,
        enable_multi_agent=True,
    )
    
    return result


if __name__ == "__main__":
    import sys
    
    demo = sys.argv[1] if len(sys.argv) > 1 else "saas"
    
    demos = {
        "saas": research_and_compare_saas_pricing,
        "jobs": multi_site_job_search,
        "products": comprehensive_product_research,
        "form": complex_multi_step_form_completion,
    }
    
    if demo in demos:
        result = demos[demo]()
        print(f"\n[COMPLETE] Demo finished with {len(result['trajectory'])} steps")
    else:
        print(f"Available demos: {', '.join(demos.keys())}")
        print(f"Usage: python {__file__} <demo_name>")
