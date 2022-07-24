import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_glue_db_table_infra.cdk_glue_db_table_infra_stack import CdkGlueDbTableInfraStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_glue_db_table_infra/cdk_glue_db_table_infra_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkGlueDbTableInfraStack(app, "cdk-glue-db-table-infra")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
