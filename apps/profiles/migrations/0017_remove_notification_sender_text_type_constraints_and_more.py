# Generated by Django 4.2.3 on 2023-10-04 15:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0016_alter_notification_text"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="notification",
            name="sender_text_type_constraints",
        ),
        migrations.RemoveConstraint(
            model_name="notification",
            name="selected_object_constraints",
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("comment", None), ("post__isnull", False), ("reply", None)
                    ),
                    models.Q(
                        ("comment__isnull", False), ("post", None), ("reply", None)
                    ),
                    models.Q(
                        ("comment", None), ("post", None), ("reply__isnull", False)
                    ),
                    models.Q(
                        ("comment", None),
                        ("ntype", "ADMIN"),
                        ("post", None),
                        ("reply", None),
                    ),
                    _connector="OR",
                ),
                name="selected_object_constraints",
                violation_error_message="\n                        * Cannot have cannot have post, comment, reply or any two of the three simultaneously. <br/>\n                        &ensp;&ensp;&nbsp;&nbsp;&nbsp;&nbsp;* If the three are None, then it must be of type 'ADMIN'\n                    ",
            ),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("ntype", "ADMIN"), ("sender", None), ("text__isnull", False)
                    ),
                    models.Q(
                        models.Q(("ntype", "ADMIN"), _negated=True),
                        ("sender__isnull", False),
                        ("text", None),
                    ),
                    _connector="OR",
                ),
                name="sender_text_type_constraints",
                violation_error_message="If No Sender, type must be ADMIN and text must not be empty and vice versa.",
            ),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        models.Q(
                            ("ntype", "ADMIN"), ("ntype", "REACTION"), _connector="OR"
                        ),
                        ("post__isnull", False),
                    ),
                    models.Q(
                        models.Q(
                            ("ntype", "COMMENT"), ("ntype", "REACTION"), _connector="OR"
                        ),
                        ("comment__isnull", False),
                    ),
                    models.Q(
                        models.Q(
                            ("ntype", "REPLY"), ("ntype", "REACTION"), _connector="OR"
                        ),
                        ("reply__isnull", False),
                    ),
                    models.Q(
                        ("comment", None),
                        ("ntype", "ADMIN"),
                        ("post", None),
                        ("reply", None),
                    ),
                    _connector="OR",
                ),
                name="post_comment_reply_type_constraints",
                violation_error_message="\n                        * If Post, type must be ADMIN or REACTION. <br/>\n                        &ensp;&ensp;&nbsp;&nbsp;&nbsp;&nbsp;* If Comment, type must be COMMENT or REACTION. <br/>\n                        &ensp;&ensp;&nbsp;&nbsp;&nbsp;&nbsp;* If Reply, type must be REPLY or REACTION. <br/>\n                    ",
            ),
        ),
    ]