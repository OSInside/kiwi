<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv81to82">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv81to82"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>8.1</literal> to <literal>8.2</literal>.
</para>
<xsl:template match="image" mode="conv81to82">
    <xsl:choose>
        <!-- nothing to do if already at 8.2 -->
        <xsl:when test="@schemaversion > 8.1">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="8.2">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv81to82"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv81to82">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv81to82"/>
    </xsl:copy>
</xsl:template>

<!-- delete use_for_bootstrap attribute from repository -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete obsolete use_for_bootstrap attribute from repository
</para>
<xsl:template match="repository" mode="conv81to82">
    <repository>
        <xsl:copy-of select="@*[not(local-name(.) = 'use_for_bootstrap')]"/>
        <xsl:apply-templates mode="conv81to82"/>
    </repository>
</xsl:template>

</xsl:stylesheet>
