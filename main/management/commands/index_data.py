from django.core.management.base import BaseCommand
from django.conf import settings
from main.opensearch_utils import get_opensearch_client, index_beir_scifact_data
import logging

# Configure basic logging for the command
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Loads BeIR/scifact data and indexes it into OpenSearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-docs',
            type=int,
            help='Maximum number of documents to index from BeIR/scifact.',
            default=None # Index all by default
        )
        parser.add_argument(
            '--skip-check',
            action='store_true',
            help='Skip dependency checking',
        )

    def check_dependencies(self):
        """Check if required dependencies are available"""
        missing_deps = []
        
        # Check spaCy
        try:
            import spacy
            try:
                spacy.load("en_core_web_sm")
            except OSError:
                self.stdout.write(self.style.WARNING(
                    'spaCy English model not found. Install with: python -m spacy download en_core_web_sm'
                ))
        except ImportError:
            missing_deps.append('spacy')
        
        # Check datasets
        try:
            import datasets
        except ImportError:
            missing_deps.append('datasets')
        
        if missing_deps:
            self.stderr.write(self.style.ERROR(
                f'Missing dependencies: {", ".join(missing_deps)}'
            ))
            self.stderr.write(self.style.ERROR(
                'Install with: pip install ' + ' '.join(missing_deps)
            ))
            return False
        
        return True

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting BeIR/scifact data indexing process...'))
        
        if not options['skip_check'] and not self.check_dependencies():
            self.stderr.write(self.style.ERROR('Dependency check failed. Use --skip-check to proceed anyway.'))
            return
        
        max_docs_to_index = options['max_docs']

        try:
            client = get_opensearch_client()
            if not client.ping():
                self.stderr.write(self.style.ERROR('Cannot connect to OpenSearch. Please check if it is running and configured correctly.'))
                return

            self.stdout.write(self.style.SUCCESS(f"Successfully connected to OpenSearch at {settings.OPENSEARCH_URL}"))
            
            index_name = settings.OPENSEARCH_INDEX_NAME
            index_beir_scifact_data(client, index_name, max_docs=max_docs_to_index)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully indexed BeIR/scifact data into "{index_name}".'))
        
        except Exception as e:
            logger.error(f"An error occurred during the BeIR/scifact indexing process: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f'An error occurred: {e}'))
