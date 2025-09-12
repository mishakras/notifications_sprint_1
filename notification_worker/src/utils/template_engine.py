from jinja2 import Template, TemplateError
from src.core import logger


class TemplateEngine:
    @staticmethod
    def render_template(template_content: str, context: dict) -> str:
        """Рендеринг шаблона с использованием Jinja2"""
        try:
            template = Template(template_content)
            return template.render(**context)
        except TemplateError as e:
            logger.error(f"Template rendering error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected template error: {str(e)}")
            raise


template_engine = TemplateEngine()
