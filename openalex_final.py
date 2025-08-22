import requests
import pandas as pd
import matplotlib.pyplot as plt
import time
from collections import defaultdict
from datetime import datetime

class OpenAlexEnergyHubCollector:
    def __init__(self, email="your.email@domain.com"):
        self.base_url = "https://api.openalex.org/"
        self.email = email
        self.papers = []
        
        # Energy hub search terms - optimized for OpenAlex
        self.search_terms = {
            'core': [
                'energy hub',
                'energy hubs',
                'energy hub optimization',
                'energy hub modeling'
            ],
            'related': [
                'multi-energy system',
                'integrated energy system',
                'multi-carrier energy',
                'energy system integration',
                'multi-energy hub',
                'energy nexus'
            ]
        }
    
    def search_works(self, search_query, category, year_start=2004, year_end=2025):
        """
        Search OpenAlex for works using their powerful search capabilities
        Based on official OpenAlex documentation and tutorials
        """
        print(f"🔍 Searching OpenAlex for: '{search_query}' ({category})")
        
        # Build filters - OpenAlex format
        filters = [
            f"publication_year:{year_start}-{year_end}",
            f"title.search:{search_query}"  # Search in title for better precision
        ]
        
        # Construct URL
        endpoint = "works"
        params = {
            'filter': ','.join(filters),
            'per-page': 200,  # Max per request
            'sort': 'publication_date:desc',
            'mailto': self.email
        }
        
        all_papers = []
        page = 1
        
        try:
            while True:
                # Add page parameter
                params['page'] = page
                
                # Make request
                response = requests.get(self.base_url + endpoint, params=params, timeout=30)
                
                if response.status_code != 200:
                    print(f"   ❌ Error {response.status_code}: {response.text}")
                    break
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    break
                
                # Process results
                for work in results:
                    paper = {
                        'id': work.get('id', ''),
                        'title': work.get('display_name', ''),
                        'year': work.get('publication_year'),
                        'doi': work.get('doi'),
                        'citation_count': work.get('cited_by_count', 0),
                        'open_access': work.get('open_access', {}).get('is_oa', False),
                        'venue': '',
                        'authors': [],
                        'abstract_inverted': work.get('abstract_inverted_index', {}),
                        'search_term': search_query,
                        'category': category,
                        'source': 'openalex'
                    }
                    
                    # Extract venue information
                    primary_location = work.get('primary_location', {})
                    if primary_location:
                        source = primary_location.get('source', {})
                        if source:
                            paper['venue'] = source.get('display_name', '')
                    
                    # Extract author information
                    authorships = work.get('authorships', [])
                    for authorship in authorships[:10]:  # Limit to first 10 authors
                        author = authorship.get('author', {})
                        if author:
                            paper['authors'].append({
                                'name': author.get('display_name', ''),
                                'orcid': author.get('orcid')
                            })
                    
                    # Only include papers from our target years
                    if paper['year'] and 2020 <= paper['year'] <= 2025:
                        all_papers.append(paper)
                
                # Check if we have more pages
                meta = data.get('meta', {})
                if page >= meta.get('count', 0) / params['per-page']:
                    break
                
                page += 1
                time.sleep(0.1)  # Be respectful to the API
                
                # Safety limit
                if page > 10:  # Max 2000 papers per search term
                    break
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print(f"   ✅ Found {len(all_papers)} papers")
        return all_papers
    
    def search_by_abstract(self, search_query, category, year_start=2020, year_end=2025):
        """
        Alternative search using abstract field for broader coverage
        """
        print(f"🔍 Abstract search for: '{search_query}' ({category})")
        
        filters = [
            f"publication_year:{year_start}-{year_end}",
            f"abstract.search:{search_query}"
        ]
        
        params = {
            'filter': ','.join(filters),
            'per-page': 100,
            'sort': 'cited_by_count:desc',  # Get most cited first
            'mailto': self.email
        }
        
        try:
            response = requests.get(self.base_url + "works", params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                papers = []
                for work in results:
                    if work.get('publication_year') and 2020 <= work.get('publication_year') <= 2025:
                        paper = {
                            'id': work.get('id', ''),
                            'title': work.get('display_name', ''),
                            'year': work.get('publication_year'),
                            'citation_count': work.get('cited_by_count', 0),
                            'search_term': search_query,
                            'category': category,
                            'source': 'openalex_abstract'
                        }
                        papers.append(paper)
                
                print(f"   ✅ Found {len(papers)} papers via abstract search")
                return papers
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        return []
    
    def collect_all_papers(self):
        """
        Collect papers using multiple search strategies
        """
        print("🚀 Starting OpenAlex Collection...")
        print("=" * 50)
        
        all_papers = []
        
        # Strategy 1: Title search (most precise)
        print("📖 Strategy 1: Title-based search")
        for category, terms in self.search_terms.items():
            for term in terms:
                papers = self.search_works(term, category)
                all_papers.extend(papers)
                time.sleep(1)
        
        # Strategy 2: Abstract search for broader coverage
        print(f"\n📄 Strategy 2: Abstract-based search")
        key_terms = ['energy hub', 'multi-energy system', 'integrated energy system']
        for term in key_terms:
            papers = self.search_by_abstract(term, 'related')
            all_papers.extend(papers)
            time.sleep(1)
        
        # Remove duplicates
        print(f"\n🔧 Removing duplicates from {len(all_papers)} papers...")
        unique_papers = self.remove_duplicates(all_papers)
        
        self.papers = unique_papers
        print(f"✅ Final dataset: {len(self.papers)} unique papers")
        
        self.print_summary()
        return self.papers
    
    def remove_duplicates(self, papers):
        """
        Remove duplicates using multiple criteria
        """
        unique_papers = []
        seen_ids = set()
        seen_titles = set()
        
        for paper in papers:
            # Use OpenAlex ID as primary deduplication
            paper_id = paper.get('id', '')
            title = str(paper.get('title', '')).lower().strip()
            
            if paper_id and paper_id not in seen_ids:
                seen_ids.add(paper_id)
                unique_papers.append(paper)
            elif title and title not in seen_titles:
                seen_titles.add(title)
                unique_papers.append(paper)
        
        return unique_papers
    
    def print_summary(self):
        """Print collection summary"""
        if not self.papers:
            return
        
        print(f"\n📊 OPENALEX COLLECTION SUMMARY:")
        print("-" * 40)
        
        # By category
        category_counts = defaultdict(int)
        year_counts = defaultdict(int)
        citation_stats = []
        
        for paper in self.papers:
            category_counts[paper.get('category', 'unknown')] += 1
            year = paper.get('year')
            if year:
                year_counts[year] += 1
            
            citations = paper.get('citation_count', 0)
            if isinstance(citations, (int, float)):
                citation_stats.append(citations)
        
        print("By Category:")
        for cat, count in sorted(category_counts.items()):
            print(f"  {cat:15s}: {count:3d} papers")
        
        print(f"\nBy Year:")
        for year in sorted(year_counts.keys()):
            print(f"  {year}: {year_counts[year]:3d} papers")
        
        if citation_stats:
            avg_citations = sum(citation_stats) / len(citation_stats)
            print(f"\nCitation Statistics:")
            print(f"  Average citations: {avg_citations:.1f}")
            print(f"  Max citations: {max(citation_stats)}")
            print(f"  Papers with >10 citations: {sum(1 for c in citation_stats if c > 10)}")
    
    def create_visualization(self):
        """Create simple visualization of the results"""
        if not self.papers:
            print("❌ No data to visualize")
            return
        
        # Prepare data
        year_counts = defaultdict(int)
        category_counts = defaultdict(int)
        
        for paper in self.papers:
            year = paper.get('year')
            if year and 2020 <= year <= 2025:
                year_counts[year] += 1
                category_counts[paper.get('category', 'unknown')] += 1
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Energy Hub Research from OpenAlex (2020-2025)', fontsize=16, fontweight='bold')
        
        # Plot 1: Papers by year
        years = sorted(year_counts.keys())
        counts = [year_counts[year] for year in years]
        
        bars = ax1.bar(years, counts, color='steelblue', alpha=0.8, edgecolor='navy')
        ax1.set_title('Publications per Year', fontweight='bold')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Number of Papers')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, count in zip(bars, counts):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        # Plot 2: Category distribution
        categories = list(category_counts.keys())
        cat_counts = list(category_counts.values())
        colors = ['#2E8B57', '#FF6B35', '#4169E1'][:len(categories)]
        
        wedges, texts, autotexts = ax2.pie(cat_counts, labels=categories, colors=colors,
                                          autopct='%1.1f%%', startangle=90)
        ax2.set_title('Research Category Distribution', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('openalex_energy_hub_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"📊 Visualization saved as: openalex_energy_hub_analysis.png")
    
    def save_to_csv(self, filename='openalex_energy_hub_papers.csv'):
        """Save papers to CSV"""
        if not self.papers:
            print("❌ No data to save")
            return
        
        # Prepare data for CSV
        csv_data = []
        for paper in self.papers:
            # Handle authors
            authors = paper.get('authors', [])
            author_names = '; '.join([author.get('name', '') for author in authors])
            
            # Reconstruct abstract from inverted index (simplified)
            abstract_inverted = paper.get('abstract_inverted', {})
            abstract_text = ""
            if abstract_inverted:
                # Simple reconstruction - full implementation would sort by position
                words = list(abstract_inverted.keys())[:50]  # First 50 words
                abstract_text = ' '.join(words)
            
            row = {
                'openalex_id': paper.get('id', ''),
                'title': paper.get('title', ''),
                'year': paper.get('year', ''),
                'authors': author_names,
                'venue': paper.get('venue', ''),
                'doi': paper.get('doi', ''),
                'citation_count': paper.get('citation_count', 0),
                'open_access': paper.get('open_access', False),
                'abstract_sample': abstract_text,
                'search_term': paper.get('search_term', ''),
                'category': paper.get('category', ''),
                'source_strategy': paper.get('source', '')
            }
            csv_data.append(row)
        
        # Save to CSV
        df = pd.DataFrame(csv_data)
        
        # Clean data
        df = df[df['year'] != '']
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df = df.dropna(subset=['year'])
        df = df[(df['year'] >= 2020) & (df['year'] <= 2025)]
        
        df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"\n📄 CSV EXPORT COMPLETE:")
        print(f"   File: {filename}")
        print(f"   Records: {len(df)}")
        print(f"   Year range: {df['year'].min():.0f} - {df['year'].max():.0f}")
        print(f"   Total citations: {df['citation_count'].sum()}")
        print(f"   Open Access papers: {df['open_access'].sum()}")
        
        return df
    
    def save_annual_summary_csvs(self):
        """
        Save detailed annual summary CSV files:
        1. Core energy hub papers by year
        2. Combined core + related papers by year
        """
        if not self.papers:
            print("❌ No data to create annual summaries")
            return
        
        print(f"\n📊 Creating Annual Summary Reports...")
        
        # Organize data by year and category
        annual_data = defaultdict(lambda: {'core': [], 'related': [], 'all': []})
        
        for paper in self.papers:
            year = paper.get('year')
            category = paper.get('category', 'unknown')
            
            if year and isinstance(year, (int, float)) and 2020 <= year <= 2025:
                year = int(year)
                annual_data[year]['all'].append(paper)
                if category in ['core', 'related']:
                    annual_data[year][category].append(paper)
        
        # Create summary statistics
        summary_stats = []
        core_papers_detail = []
        combined_papers_detail = []
        
        for year in sorted(annual_data.keys()):
            year_data = annual_data[year]
            core_count = len(year_data['core'])
            related_count = len(year_data['related'])
            total_count = core_count + related_count
            
            # Calculate statistics
            core_citations = sum(p.get('citation_count', 0) for p in year_data['core'])
            related_citations = sum(p.get('citation_count', 0) for p in year_data['related'])
            total_citations = core_citations + related_citations
            
            core_avg_citations = core_citations / core_count if core_count > 0 else 0
            related_avg_citations = related_citations / related_count if related_count > 0 else 0
            total_avg_citations = total_citations / total_count if total_count > 0 else 0
            
            # Count open access papers
            core_oa = sum(1 for p in year_data['core'] if p.get('open_access', False))
            related_oa = sum(1 for p in year_data['related'] if p.get('open_access', False))
            total_oa = core_oa + related_oa
            
            # Summary statistics row
            summary_stats.append({
                'year': year,
                'core_papers': core_count,
                'related_papers': related_count,
                'total_papers': total_count,
                'core_citations': core_citations,
                'related_citations': related_citations,
                'total_citations': total_citations,
                'core_avg_citations': round(core_avg_citations, 2),
                'related_avg_citations': round(related_avg_citations, 2),
                'total_avg_citations': round(total_avg_citations, 2),
                'core_open_access': core_oa,
                'related_open_access': related_oa,
                'total_open_access': total_oa,
                'core_oa_percentage': round((core_oa/core_count)*100, 1) if core_count > 0 else 0,
                'related_oa_percentage': round((related_oa/related_count)*100, 1) if related_count > 0 else 0,
                'total_oa_percentage': round((total_oa/total_count)*100, 1) if total_count > 0 else 0
            })
            
            # Detailed core papers
            for paper in year_data['core']:
                authors = '; '.join([a.get('name', '') for a in paper.get('authors', [])[:5]])  # First 5 authors
                core_papers_detail.append({
                    'year': year,
                    'title': paper.get('title', ''),
                    'authors': authors,
                    'venue': paper.get('venue', ''),
                    'citation_count': paper.get('citation_count', 0),
                    'open_access': paper.get('open_access', False),
                    'doi': paper.get('doi', ''),
                    'openalex_id': paper.get('id', ''),
                    'search_term': paper.get('search_term', ''),
                    'category': 'core'
                })
            
            # Detailed combined papers (core + related)
            for paper in year_data['all']:
                if paper.get('category') in ['core', 'related']:
                    authors = '; '.join([a.get('name', '') for a in paper.get('authors', [])[:5]])
                    combined_papers_detail.append({
                        'year': year,
                        'title': paper.get('title', ''),
                        'authors': authors,
                        'venue': paper.get('venue', ''),
                        'citation_count': paper.get('citation_count', 0),
                        'open_access': paper.get('open_access', False),
                        'doi': paper.get('doi', ''),
                        'openalex_id': paper.get('id', ''),
                        'search_term': paper.get('search_term', ''),
                        'category': paper.get('category', 'unknown')
                    })
        
        # Save CSV files
        
        # 1. Annual Summary Statistics
        summary_df = pd.DataFrame(summary_stats)
        summary_filename = 'energy_hub_annual_summary.csv'
        summary_df.to_csv(summary_filename, index=False)
        
        # 2. Core Papers Only - Detailed
        core_df = pd.DataFrame(core_papers_detail)
        core_filename = 'energy_hub_core_papers_by_year.csv'
        core_df.to_csv(core_filename, index=False)
        
        # 3. Combined Core + Related Papers - Detailed  
        combined_df = pd.DataFrame(combined_papers_detail)
        combined_filename = 'energy_hub_core_plus_related_papers_by_year.csv'
        combined_df.to_csv(combined_filename, index=False)
        
        # 4. Create a simple year-count matrix CSV
        year_count_matrix = []
        for year in sorted(annual_data.keys()):
            year_data = annual_data[year]
            year_count_matrix.append({
                'year': year,
                'core_count': len(year_data['core']),
                'related_count': len(year_data['related']),
                'total_count': len(year_data['core']) + len(year_data['related'])
            })
        
        matrix_df = pd.DataFrame(year_count_matrix)
        matrix_filename = 'energy_hub_paper_counts_by_year.csv'
        matrix_df.to_csv(matrix_filename, index=False)
        
        # Print summary
        print(f"\n📄 ANNUAL SUMMARY FILES CREATED:")
        print(f"   1. {summary_filename} - Complete annual statistics")
        print(f"   2. {core_filename} - Core energy hub papers only ({len(core_df)} papers)")
        print(f"   3. {combined_filename} - Core + related papers ({len(combined_df)} papers)")
        print(f"   4. {matrix_filename} - Simple year/count matrix")
        
        print(f"\n📊 PUBLICATION TRENDS:")
        for _, row in summary_df.iterrows():
            print(f"   {int(row['year'])}: {int(row['core_papers'])} core, {int(row['related_papers'])} related, {int(row['total_papers'])} total")
        
        # Calculate growth rates
        if len(summary_df) > 1:
            print(f"\n📈 GROWTH ANALYSIS:")
            for i in range(1, len(summary_df)):
                prev_total = summary_df.iloc[i-1]['total_papers']
                curr_total = summary_df.iloc[i]['total_papers']
                growth = ((curr_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
                year = int(summary_df.iloc[i]['year'])
                print(f"   {year}: {growth:+.1f}% growth ({int(prev_total)} → {int(curr_total)} papers)")
        
        return {
            'summary': summary_df,
            'core_papers': core_df, 
            'combined_papers': combined_df,
            'year_matrix': matrix_df
        }
    
    def create_publication_trend_chart(self):
        """Create a detailed publication trend visualization"""
        if not self.papers:
            print("❌ No data for trend chart")
            return
        
        # Prepare data
        annual_data = defaultdict(lambda: {'core': 0, 'related': 0})
        
        for paper in self.papers:
            year = paper.get('year')
            category = paper.get('category', 'unknown')
            
            if year and isinstance(year, (int, float)) and 2020 <= year <= 2025:
                year = int(year)
                if category in ['core', 'related']:
                    annual_data[year][category] += 1
        
        years = sorted(annual_data.keys())
        core_counts = [annual_data[year]['core'] for year in years]
        related_counts = [annual_data[year]['related'] for year in years]
        total_counts = [core_counts[i] + related_counts[i] for i in range(len(years))]
        
        # Create comprehensive visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Energy Hub Research Publication Trends (OpenAlex Data)', fontsize=16, fontweight='bold')
        
        # Plot 1: Stacked bar chart
        width = 0.6
        ax1.bar(years, core_counts, width, label='Core Energy Hub', color='#2E8B57', alpha=0.8)
        ax1.bar(years, related_counts, width, bottom=core_counts, label='Related Multi-Energy', color='#FF6B35', alpha=0.8)
        
        ax1.set_title('Annual Publications by Category', fontweight='bold')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Number of Papers')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for i, year in enumerate(years):
            total = total_counts[i]
            ax1.text(year, total + 1, str(total), ha='center', va='bottom', fontweight='bold')
        
        # Plot 2: Line plot trends
        ax2.plot(years, core_counts, 'o-', linewidth=3, markersize=8, label='Core Energy Hub', color='#2E8B57')
        ax2.plot(years, related_counts, 's-', linewidth=3, markersize=8, label='Related Multi-Energy', color='#FF6B35')
        ax2.plot(years, total_counts, '^-', linewidth=3, markersize=8, label='Total', color='#4169E1')
        
        ax2.set_title('Publication Trend Lines', fontweight='bold')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Number of Papers')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Growth rates
        growth_rates = []
        for i in range(1, len(total_counts)):
            if total_counts[i-1] > 0:
                growth = ((total_counts[i] - total_counts[i-1]) / total_counts[i-1]) * 100
                growth_rates.append(growth)
            else:
                growth_rates.append(0)
        
        if growth_rates:
            colors = ['green' if x >= 0 else 'red' for x in growth_rates]
            bars = ax3.bar(years[1:], growth_rates, color=colors, alpha=0.7)
            ax3.set_title('Year-over-Year Growth Rate', fontweight='bold')
            ax3.set_xlabel('Year')
            ax3.set_ylabel('Growth Rate (%)')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax3.grid(True, alpha=0.3)
            
            # Add value labels
            for bar, rate in zip(bars, growth_rates):
                ax3.text(bar.get_x() + bar.get_width()/2, 
                        bar.get_height() + (2 if rate >= 0 else -4),
                        f'{rate:.1f}%', ha='center', va='bottom' if rate >= 0 else 'top')
        
        # Plot 4: Cumulative publications
        cumulative_total = [sum(total_counts[:i+1]) for i in range(len(total_counts))]
        cumulative_core = [sum(core_counts[:i+1]) for i in range(len(core_counts))]
        
        ax4.plot(years, cumulative_total, 'o-', linewidth=4, markersize=10, color='purple', label='Total Cumulative')
        ax4.plot(years, cumulative_core, 's-', linewidth=3, markersize=8, color='darkgreen', label='Core Cumulative')
        ax4.fill_between(years, cumulative_total, alpha=0.3, color='purple')
        
        ax4.set_title('Cumulative Publications Over Time', fontweight='bold')
        ax4.set_xlabel('Year')
        ax4.set_ylabel('Cumulative Papers')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (year, cum) in enumerate(zip(years, cumulative_total)):
            ax4.text(year, cum + 2, str(cum), ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('energy_hub_publication_trends.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"📊 Detailed trend chart saved as: energy_hub_publication_trends.png")
        
        return years, core_counts, related_counts, total_counts

def run_openalex_collection():
    """Run basic OpenAlex collection (original function)"""
    email = input("Enter your email for faster API responses: ").strip()
    if not email:
        email = "researcher@example.com"
    
    collector = OpenAlexEnergyHubCollector(email=email)
    papers = collector.collect_all_papers()
    
    if papers:
        collector.create_visualization()
        df = collector.save_to_csv()
        print(f"\n✅ Basic collection complete: {len(papers)} papers")
        return collector, df
    else:
        print("❌ No papers collected")
        return None, None
def run_complete_analysis():
    """Run complete OpenAlex analysis with all CSV outputs"""
    email = input("Enter your email for faster API responses: ").strip()
    if not email:
        email = "researcher@example.com"
    
    print(f"\n🚀 Starting Complete Energy Hub Analysis...")
    collector = OpenAlexEnergyHubCollector(email=email)
    
    # Step 1: Collect papers
    print(f"\n📚 Step 1: Collecting papers from OpenAlex...")
    papers = collector.collect_all_papers()
    
    if not papers:
        print("❌ No papers collected. Exiting.")
        return None, None
    
    # Step 2: Create visualizations
    print(f"\n📊 Step 2: Creating visualizations...")
    collector.create_visualization()
    collector.create_publication_trend_chart()
    
    # Step 3: Save detailed CSV files
    print(f"\n💾 Step 3: Saving CSV files...")
    main_df = collector.save_to_csv()
    annual_reports = collector.save_annual_summary_csvs()
    
    # Step 4: Print final summary
    print(f"\n" + "="*60)
    print(f"                    ANALYSIS COMPLETE!")
    print(f"="*60)
    print(f"📊 Papers collected: {len(papers)}")
    print(f"📁 Files created:")
    print(f"   • openalex_energy_hub_papers.csv (all papers)")
    print(f"   • energy_hub_annual_summary.csv (statistics by year)")
    print(f"   • energy_hub_core_papers_by_year.csv (core papers only)")
    print(f"   • energy_hub_core_plus_related_papers_by_year.csv (core + related)")
    print(f"   • energy_hub_paper_counts_by_year.csv (simple counts)")
    print(f"📈 Charts created:")
    print(f"   • openalex_energy_hub_analysis.png")
    print(f"   • energy_hub_publication_trends.png")
    
    # Quick stats
    if annual_reports:
        summary_df = annual_reports['summary']
        total_papers = summary_df['total_papers'].sum()
        total_core = summary_df['core_papers'].sum()
        total_related = summary_df['related_papers'].sum()
        
        print(f"\n📈 Key Statistics:")
        print(f"   • Total core papers: {total_core}")
        print(f"   • Total related papers: {total_related}")
        print(f"   • Research period: {summary_df['year'].min():.0f}-{summary_df['year'].max():.0f}")
        print(f"   • Average papers per year: {total_papers/len(summary_df):.1f}")
        
        # Find peak year
        peak_year_idx = summary_df['total_papers'].idxmax()
        peak_year = summary_df.loc[peak_year_idx, 'year']
        peak_count = summary_df.loc[peak_year_idx, 'total_papers']
        print(f"   • Peak publication year: {peak_year:.0f} ({peak_count:.0f} papers)")
    
    print(f"="*60)
    
    return collector, annual_reports

def create_research_summary_report():
    """Create a formatted research summary for your mini review paper"""
    email = input("Enter your email: ").strip() or "researcher@example.com"
    
    collector = OpenAlexEnergyHubCollector(email=email)
    papers = collector.collect_all_papers()
    
    if not papers:
        return
    
    # Generate all reports
    annual_reports = collector.save_annual_summary_csvs()
    
    # Create a formatted summary for academic use
    report_filename = 'energy_hub_research_summary_report.txt'
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("           ENERGY HUB RESEARCH BIBLIOMETRIC ANALYSIS\n")
        f.write("                    (OpenAlex Database)\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"ANALYSIS DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"DATA SOURCE: OpenAlex (https://openalex.org/)\n")
        f.write(f"SEARCH PERIOD: 2020-2025\n")
        f.write(f"TOTAL PAPERS COLLECTED: {len(papers)}\n\n")
        
        if annual_reports:
            summary_df = annual_reports['summary']
            
            f.write("ANNUAL PUBLICATION STATISTICS:\n")
            f.write("-" * 50 + "\n")
            f.write(f"{'Year':<6} {'Core':<6} {'Related':<8} {'Total':<6} {'Growth':<8} {'Citations':<10}\n")
            f.write("-" * 50 + "\n")
            
            for i, row in summary_df.iterrows():
                if i > 0:
                    prev_total = summary_df.iloc[i-1]['total_papers']
                    growth = ((row['total_papers'] - prev_total) / prev_total * 100) if prev_total > 0 else 0
                    growth_str = f"{growth:+5.1f}%"
                else:
                    growth_str = "  -   "
                
                f.write(f"{int(row['year']):<6} {int(row['core_papers']):<6} {int(row['related_papers']):<8} "
                       f"{int(row['total_papers']):<6} {growth_str:<8} {int(row['total_citations']):<10}\n")
            
            f.write("\nKEY FINDINGS:\n")
            f.write("-" * 20 + "\n")
            
            total_papers = summary_df['total_papers'].sum()
            total_core = summary_df['core_papers'].sum()
            total_related = summary_df['related_papers'].sum()
            
            f.write(f"• Research Focus Distribution:\n")
            f.write(f"  - Core energy hub research: {total_core} papers ({total_core/total_papers*100:.1f}%)\n")
            f.write(f"  - Related multi-energy research: {total_related} papers ({total_related/total_papers*100:.1f}%)\n\n")
            
            f.write(f"• Publication Growth:\n")
            first_year_total = summary_df.iloc[0]['total_papers']
            last_year_total = summary_df.iloc[-1]['total_papers']
            overall_growth = ((last_year_total - first_year_total) / first_year_total * 100) if first_year_total > 0 else 0
            f.write(f"  - Overall growth: {overall_growth:+.1f}% from {summary_df.iloc[0]['year']:.0f} to {summary_df.iloc[-1]['year']:.0f}\n")
            f.write(f"  - Average annual publications: {total_papers/len(summary_df):.1f} papers\n\n")
            
            f.write(f"• Citation Impact:\n")
            total_citations = summary_df['total_citations'].sum()
            avg_citations = total_citations / total_papers if total_papers > 0 else 0
            f.write(f"  - Total citations: {int(total_citations)}\n")
            f.write(f"  - Average citations per paper: {avg_citations:.1f}\n\n")
            
            peak_year_idx = summary_df['total_papers'].idxmax()
            peak_year = summary_df.loc[peak_year_idx, 'year']
            peak_count = summary_df.loc[peak_year_idx, 'total_papers']
            f.write(f"• Peak Publication Year: {peak_year:.0f} ({peak_count:.0f} papers)\n\n")
            
        f.write("METHODOLOGY:\n")
        f.write("-" * 15 + "\n")
        f.write("• Database: OpenAlex comprehensive scholarly database\n")
        f.write("• Search Strategy: Multi-term approach covering:\n")
        f.write("  - Core terms: 'energy hub', 'energy hubs', 'energy hub optimization'\n")
        f.write("  - Related terms: 'multi-energy system', 'integrated energy system'\n")
        f.write("• Search Fields: Title and abstract\n")
        f.write("• Time Period: 2020-2025\n")
        f.write("• Deduplication: Based on OpenAlex IDs and title matching\n\n")
        
        f.write("LIMITATIONS:\n")
        f.write("-" * 13 + "\n")
        f.write("• OpenAlex coverage may not include all energy hub publications\n")
        f.write("• Search limited to English-language metadata\n")
        f.write("• 2025 data represents partial year only\n")
        f.write("• Citation counts may lag for recent publications\n\n")
        
        f.write("RECOMMENDED CITATION:\n")
        f.write("-" * 20 + "\n")
        f.write("Data retrieved from OpenAlex (https://openalex.org/) on ")
        f.write(f"{datetime.now().strftime('%Y-%m-%d')}. \n")
        f.write("OpenAlex is developed by OurResearch and provides open access to scholarly metadata.\n\n")
        
        f.write("="*80 + "\n")
    
    print(f"\n📋 Research summary report created: {report_filename}")
    print(f"   This file contains a formatted summary suitable for your mini review paper.")
    
    return annual_reports
    """Run OpenAlex collection with your email"""
    email = input("Enter your email for faster API responses: ").strip()
    if not email:
        email = "researcher@example.com"  # Default
    
    collector = OpenAlexEnergyHubCollector(email=email)
    
    # Collect papers
    papers = collector.collect_all_papers()
    
    if papers:
        # Create visualization
        collector.create_visualization()
        
        # Save to CSV
        df = collector.save_to_csv()
        
        print(f"\n✅ SUCCESS!")
        print(f"   Papers collected: {len(papers)}")
        print(f"   Visualization: openalex_energy_hub_analysis.png")
        print(f"   Data: openalex_energy_hub_papers.csv")
        
        return collector, df
    else:
        print("❌ No papers collected")
        return None, None

def quick_openalex_test():
    """Quick test with a single search term"""
    collector = OpenAlexEnergyHubCollector()
    
    # Test with one term
    papers = collector.search_works("energy hub", "core", 2020, 2025)
    
    print(f"\n🧪 QUICK TEST RESULTS:")
    print(f"   Found {len(papers)} papers for 'energy hub'")
    
    if papers:
        recent_papers = [p for p in papers if p.get('year', 0) >= 2023]
        print(f"   Recent papers (2023+): {len(recent_papers)}")
        
        if recent_papers:
            print(f"\n📋 Sample recent papers:")
            for i, paper in enumerate(recent_papers[:3]):
                print(f"   {i+1}. {paper.get('title', 'No title')[:80]}...")
                print(f"      Year: {paper.get('year')}, Citations: {paper.get('citation_count', 0)}")
    
    return papers

if __name__ == "__main__":
    print("OpenAlex Energy Hub Research Collector")
    print("=" * 50)
    
    choice = input("""
Choose analysis option:
1. Complete analysis (recommended) - All CSV files + charts
2. Research summary report - Formatted for academic use  
3. Basic collection - Simple CSV + chart
4. Quick test - Test functionality

Enter choice (1-4): """).strip()
    
    if choice == '1':
        collector, reports = run_complete_analysis()
    elif choice == '2':
        reports = create_research_summary_report()
    elif choice == '3':
        collector, df = run_openalex_collection()
    elif choice == '4':
        papers = quick_openalex_test()
    else:
        print("Invalid choice. Running complete analysis...")
        collector, reports = run_complete_analysis()