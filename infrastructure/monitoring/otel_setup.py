from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor

def setup_otel():
    # Set up tracer provider
    provider = TracerProvider()
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Instrument frameworks
    DjangoInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    CeleryInstrumentor().instrument()
