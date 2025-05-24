"""
Information Retrieval Evaluation Framework for ESEMPEHA Search Engine

This module provides comprehensive evaluation metrics for the search engine,
including traditional IR metrics and modern evaluation approaches.

Usage:
    python ir_eval.py --run-all
    python ir_eval.py --query "virus" --method traditional
    python ir_eval.py --create-test-queries
"""

import os
import sys
import django
import json
import numpy as np
import pandas as pd
from collections import defaultdict
from typing import List, Dict, Set, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import argparse

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esempeha.settings')
django.setup()

from django.conf import settings
from main.opensearch_utils import get_opensearch_client, search_documents
from main.semantic_search import semantic_engine
from main.text_preprocessing import preprocessor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IREvaluator:
    def __init__(self):
        self.client = get_opensearch_client()
        self.index_name = settings.OPENSEARCH_INDEX_NAME
        self.results = {}
        
    def load_test_queries(self, queries_file=None):
        """Load test queries and relevance judgments"""
        if queries_file and os.path.exists(queries_file):
            with open(queries_file, 'r') as f:
                return json.load(f)
        else:
            # Create sample test queries for SciFact domain
            return self.create_sample_queries()
    
    def create_sample_queries(self):
        """Create sample test queries for evaluation"""
        return {
            "virus": {
                "query": "virus",
                "relevant_terms": ["viral", "viruses", "pathogen", "infection"],
                "description": "Documents about viruses and viral infections"
            },
            "bacteria": {
                "query": "bacteria",
                "relevant_terms": ["bacterial", "microbe", "prokaryote", "microorganism"],
                "description": "Documents about bacteria and bacterial processes"
            },
            "protein": {
                "query": "protein",
                "relevant_terms": ["enzyme", "peptide", "amino acid", "polypeptide"],
                "description": "Documents about proteins and protein function"
            },
            "immune_system": {
                "query": "immune system",
                "relevant_terms": ["immunity", "antibody", "immunological", "defense"],
                "description": "Documents about immune system and immunology"
            },
            "covid": {
                "query": "covid-19",
                "relevant_terms": ["coronavirus", "sars-cov-2", "pandemic", "covid"],
                "description": "Documents about COVID-19 and coronavirus"
            },
            "cancer": {
                "query": "cancer",
                "relevant_terms": ["tumor", "oncology", "malignant", "carcinoma"],
                "description": "Documents about cancer and oncology"
            },
            "cell_division": {
                "query": "cell division",
                "relevant_terms": ["mitosis", "meiosis", "chromosome", "cellular"],
                "description": "Documents about cell division processes"
            },
            "dna": {
                "query": "dna",
                "relevant_terms": ["genetic", "nucleic acid", "genome", "gene"],
                "description": "Documents about DNA and genetics"
            }
        }
    
    def save_test_queries(self, filename='test_queries.json'):
        """Save test queries to file"""
        queries = self.create_sample_queries()
        with open(filename, 'w') as f:
            json.dump(queries, f, indent=2)
        print(f"Test queries saved to {filename}")
    
    def calculate_precision_recall(self, retrieved_docs: List[str], 
                                 relevant_docs: Set[str]) -> Tuple[float, float]:
        """Calculate precision and recall"""
        if not retrieved_docs:
            return 0.0, 0.0
        
        retrieved_set = set(retrieved_docs)
        relevant_retrieved = retrieved_set.intersection(relevant_docs)
        
        precision = len(relevant_retrieved) / len(retrieved_set) if retrieved_set else 0.0
        recall = len(relevant_retrieved) / len(relevant_docs) if relevant_docs else 0.0
        
        return precision, recall
    
    def calculate_f1_score(self, precision: float, recall: float) -> float:
        """Calculate F1 score"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    def calculate_average_precision(self, retrieved_docs: List[str], 
                                  relevant_docs: Set[str]) -> float:
        """Calculate Average Precision (AP)"""
        if not relevant_docs:
            return 0.0
        
        precisions = []
        relevant_count = 0
        
        for i, doc_id in enumerate(retrieved_docs):
            if doc_id in relevant_docs:
                relevant_count += 1
                precision_at_i = relevant_count / (i + 1)
                precisions.append(precision_at_i)
        
        return np.mean(precisions) if precisions else 0.0
    
    def calculate_dcg(self, relevance_scores: List[float], k: int = None) -> float:
        """Calculate Discounted Cumulative Gain"""
        if k is not None:
            relevance_scores = relevance_scores[:k]
        
        dcg = 0.0
        for i, score in enumerate(relevance_scores):
            dcg += score / np.log2(i + 2)  # i+2 because log2(1) = 0
        
        return dcg
    
    def calculate_ndcg(self, retrieved_docs: List[str], 
                      relevance_scores: Dict[str, float], k: int = 10) -> float:
        """Calculate Normalized Discounted Cumulative Gain"""
        # Get relevance scores for retrieved documents
        retrieved_scores = [relevance_scores.get(doc_id, 0.0) for doc_id in retrieved_docs[:k]]
        
        # Calculate DCG
        dcg = self.calculate_dcg(retrieved_scores, k)
        
        # Calculate IDCG (Ideal DCG)
        ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
        idcg = self.calculate_dcg(ideal_scores, k)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def get_relevant_documents(self, query_info: Dict) -> Set[str]:
        """Identify relevant documents for a query"""
        query = query_info["query"]
        relevant_terms = query_info.get("relevant_terms", [])
        
        all_terms = [query] + relevant_terms
        relevant_docs = set()
        
        for term in all_terms:
            results = search_documents(self.client, self.index_name, term, size=50)
            for result in results:
                doc_id = result.get('doc_id', result.get('id'))
                if doc_id:
                    relevant_docs.add(doc_id)
        
        return relevant_docs
    
    def calculate_relevance_scores(self, query_info: Dict, 
                                 retrieved_docs: List[str]) -> Dict[str, float]:
        """Calculate relevance scores for documents"""
        query = query_info["query"]
        relevant_terms = query_info.get("relevant_terms", [])
        
        scores = {}
        
        # Get document details
        for doc_id in retrieved_docs:
            try:
                response = self.client.get(index=self.index_name, id=doc_id)
                doc = response["_source"]
                
                title = doc.get("title", "").lower()
                text = doc.get("text", "").lower()
                combined_text = f"{title} {text}"
                
                score = 0.0
                
                if query.lower() in combined_text:
                    score += 2.0
                
                for term in relevant_terms:
                    if term.lower() in combined_text:
                        score += 1.0
                
                word_count = len(combined_text.split())
                if word_count > 0:
                    score = score / np.log(word_count + 1)
                
                scores[doc_id] = score
                
            except Exception as e:
                logger.warning(f"Could not retrieve document {doc_id}: {e}")
                scores[doc_id] = 0.0
        
        return scores
    
    def evaluate_query(self, query_info: Dict, use_semantic: bool = False) -> Dict:
        """Evaluate a single query"""
        query = query_info["query"]
        logger.info(f"Evaluating query: {query}")
        
        # Get search results
        results = search_documents(
            self.client, 
            self.index_name, 
            query, 
            size=20,
            use_semantic=use_semantic
        )
        
        retrieved_docs = [result.get('doc_id', result.get('id')) for result in results]
        retrieved_docs = [doc_id for doc_id in retrieved_docs if doc_id]
        
        # Get relevant documents
        relevant_docs = self.get_relevant_documents(query_info)
        
        # Calculate metrics
        precision, recall = self.calculate_precision_recall(retrieved_docs, relevant_docs)
        f1_score = self.calculate_f1_score(precision, recall)
        avg_precision = self.calculate_average_precision(retrieved_docs, relevant_docs)
        
        relevance_scores = self.calculate_relevance_scores(query_info, retrieved_docs)
        ndcg_10 = self.calculate_ndcg(retrieved_docs, relevance_scores, k=10)
        ndcg_20 = self.calculate_ndcg(retrieved_docs, relevance_scores, k=20)
        
        return {
            "query": query,
            "method": "semantic" if use_semantic else "traditional",
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "average_precision": avg_precision,
            "ndcg_10": ndcg_10,
            "ndcg_20": ndcg_20,
            "num_retrieved": len(retrieved_docs),
            "num_relevant": len(relevant_docs),
            "relevant_retrieved": len(set(retrieved_docs).intersection(relevant_docs))
        }
    
    def evaluate_all_queries(self, test_queries: Dict, use_semantic: bool = False) -> List[Dict]:
        """Evaluate all test queries"""
        results = []
        
        for query_id, query_info in test_queries.items():
            try:
                result = self.evaluate_query(query_info, use_semantic)
                result["query_id"] = query_id
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating query {query_id}: {e}")
        
        return results
    
    def calculate_overall_metrics(self, results: List[Dict]) -> Dict:
        """Calculate overall system metrics"""
        if not results:
            return {}
        
        df = pd.DataFrame(results)
        
        overall = {
            "mean_precision": df["precision"].mean(),
            "mean_recall": df["recall"].mean(),
            "mean_f1": df["f1_score"].mean(),
            "mean_average_precision": df["average_precision"].mean(),
            "mean_ndcg_10": df["ndcg_10"].mean(),
            "mean_ndcg_20": df["ndcg_20"].mean(),
            "total_queries": len(results),
            "total_retrieved": df["num_retrieved"].sum(),
            "total_relevant": df["num_relevant"].sum(),
            "total_relevant_retrieved": df["relevant_retrieved"].sum()
        }
        
        return overall
    
    def compare_methods(self, test_queries: Dict) -> pd.DataFrame:
        """Compare traditional vs semantic search"""
        traditional_results = self.evaluate_all_queries(test_queries, use_semantic=False)
        semantic_results = self.evaluate_all_queries(test_queries, use_semantic=True)
        
        all_results = traditional_results + semantic_results
        df = pd.DataFrame(all_results)
        
        traditional_overall = self.calculate_overall_metrics(traditional_results)
        semantic_overall = self.calculate_overall_metrics(semantic_results)
        
        comparison = pd.DataFrame({
            'Traditional': traditional_overall,
            'Semantic': semantic_overall
        })
        
        return df, comparison
    
    def plot_results(self, df: pd.DataFrame, save_path: str = 'evaluation_results.png'):
        """Plot evaluation results"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Precision comparison
        sns.barplot(data=df, x='query_id', y='precision', hue='method', ax=axes[0,0])
        axes[0,0].set_title('Precision by Query')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # Recall comparison
        sns.barplot(data=df, x='query_id', y='recall', hue='method', ax=axes[0,1])
        axes[0,1].set_title('Recall by Query')
        axes[0,1].tick_params(axis='x', rotation=45)
        
        # F1 Score comparison
        sns.barplot(data=df, x='query_id', y='f1_score', hue='method', ax=axes[1,0])
        axes[1,0].set_title('F1 Score by Query')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # NDCG@10 comparison
        sns.barplot(data=df, x='query_id', y='ndcg_10', hue='method', ax=axes[1,1])
        axes[1,1].set_title('NDCG@10 by Query')
        axes[1,1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Plot saved to {save_path}")
    
    def save_results(self, results: List[Dict], filename: str = None):
        """Save evaluation results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ir_evaluation_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {filename}")
    
    def run_comprehensive_evaluation(self):
        """Run comprehensive evaluation of the IR system"""
        print("=== ESEMPEHA Search Engine Evaluation ===")
        print(f"Index: {self.index_name}")
        print(f"Timestamp: {datetime.now()}")
        print()
        
        # Load test queries
        test_queries = self.load_test_queries()
        print(f"Loaded {len(test_queries)} test queries")
        
        # Compare methods
        print("\nComparing Traditional vs Semantic Search...")
        df, comparison = self.compare_methods(test_queries)
        
        # Display comparison
        print("\n=== Overall Metrics Comparison ===")
        print(comparison.round(4))
        
        # Save detailed results
        all_results = df.to_dict('records')
        self.save_results(all_results)
        
        # Plot results
        try:
            self.plot_results(df)
        except Exception as e:
            print(f"Error creating plots: {e}")
        
        # Print detailed results by query
        print("\n=== Detailed Results by Query ===")
        for method in ['traditional', 'semantic']:
            print(f"\n{method.upper()} SEARCH:")
            method_df = df[df['method'] == method]
            for _, row in method_df.iterrows():
                print(f"  {row['query_id']}: P={row['precision']:.3f}, R={row['recall']:.3f}, F1={row['f1_score']:.3f}, NDCG@10={row['ndcg_10']:.3f}")
        
        return df, comparison

def main():
    parser = argparse.ArgumentParser(description='IR Evaluation for ESEMPEHA Search Engine')
    parser.add_argument('--run-all', action='store_true', help='Run comprehensive evaluation')
    parser.add_argument('--query', type=str, help='Evaluate specific query')
    parser.add_argument('--method', choices=['traditional', 'semantic'], default='traditional', 
                       help='Search method to use')
    parser.add_argument('--create-test-queries', action='store_true', 
                       help='Create and save test queries file')
    
    args = parser.parse_args()
    
    evaluator = IREvaluator()
    
    if args.create_test_queries:
        evaluator.save_test_queries()
        return
    
    if args.run_all:
        evaluator.run_comprehensive_evaluation()
    elif args.query:
        # Evaluate single query
        test_queries = evaluator.load_test_queries()
        query_info = None
        
        # Find query in test set or create new one
        for qid, qinfo in test_queries.items():
            if qinfo['query'].lower() == args.query.lower():
                query_info = qinfo
                break
        
        if not query_info:
            query_info = {
                'query': args.query,
                'relevant_terms': [],
                'description': f'Custom query: {args.query}'
            }
        
        use_semantic = args.method == 'semantic'
        result = evaluator.evaluate_query(query_info, use_semantic)
        
        print(f"\n=== Evaluation Results for '{args.query}' ({args.method}) ===")
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
