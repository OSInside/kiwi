<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- default rule -->
<xsl:template match="*" mode="conv43to44">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv43to44"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>4.3</literal> to <literal>4.4</literal>.
</para>
<xsl:template match="image" mode="conv43to44">
    <xsl:choose>
        <!-- nothing to do if already at 4.4 -->
        <xsl:when test="@schemaversion > 4.3">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="4.4">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv43to44"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv43to44">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv43to44"/>
    </xsl:copy>
</xsl:template>

<!-- remove commandline element -->
<para xmlns="http://docbook.org/ns/docbook">
    Remove compressed element as it was moved into the type
    represented as attribute kernelcmdline
</para>
<xsl:template match="node()|@*">
    <xsl:copy>
        <xsl:apply-templates select="node()|@*" mode="conv43to44"/>
    </xsl:copy>
</xsl:template>
<xsl:template match="commandline" mode="conv43to44"/>

</xsl:stylesheet>
