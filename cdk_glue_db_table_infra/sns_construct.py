"""Code for generating the SNS Topic. Also used to add an email subscription to a topic."""
from aws_cdk import aws_iam as iam
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subscriptions
from aws_cdk.core import Stack


class SNSConstruct:
    """Class with static methods that are used to build and deploy SNS Topic."""
    
    @staticmethod
    def create_sns_topic(
        stack: Stack,
        env: str,
        config: dict) -> sns.Topic:
        """Creates SNS Topic and adds to the input stack."""
        return sns.Topic(
            scope=stack,
            id=f"{config['global']['app-name']}-sns-topic-id",
            display_name=f"{config['global']['source-id-short']} Reservoir Topic",
            topic_name=f"{config['global']['app-name']}-sns-topic"
        )
        
        
    @staticmethod
    def subscribe_email(
        env: str,
        config: dict,
        topic: sns.Topic) -> None:
        """Creates SNS email subscription to the input topic."""
        topic.add_subscription(
            subscriptions.EmailSubscription(email_address=config['global']['email'])
        )
        
        
    @staticmethod
    def get_sns_publish_policy(sns_topic_arn: str) -> iam.PolicyStatement:
        """Returns policy statement for publishing to an sns topic."""
        policy_statement = iam.PolicyStatement()
        policy_statement.effect = iam.Effect.ALLOW
        policy_statement.add_actions("sns:Publish")
        policy_statement.add_resources(sns_topic_arn)
        return policy_statement