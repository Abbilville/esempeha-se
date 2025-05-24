from django.core.management.base import BaseCommand
from main.semantic_search import semantic_engine
from main.query_correction import query_corrector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Build semantic search index and custom dictionary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-embeddings',
            action='store_true',
            help='Skip building document embeddings',
        )
        parser.add_argument(
            '--skip-dictionary',
            action='store_true',
            help='Skip building custom dictionary',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Building semantic search capabilities...'))
        
        try:
            if not options['skip_embeddings']:
                self.stdout.write('Building document embeddings...')
                if semantic_engine.build_document_embeddings():
                    self.stdout.write(self.style.SUCCESS('Document embeddings built successfully'))
                else:
                    self.stdout.write(self.style.WARNING('Failed to build document embeddings'))
            
            if not options['skip_dictionary']:
                self.stdout.write('Building custom dictionary for spell checking...')
                # Force rebuild of the dictionary
                query_corrector.build_custom_dictionary_from_index()
                self.stdout.write(self.style.SUCCESS('Custom dictionary built successfully'))
            
            self.stdout.write(self.style.SUCCESS('Semantic search setup completed'))
            self.stdout.write('You can now test autocomplete and spell correction features!')
        
        except Exception as e:
            logger.error(f"Error during semantic setup: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f'An error occurred: {e}'))
