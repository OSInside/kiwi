<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv70to71">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv70to71"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>7.0</literal> to <literal>7.1</literal>.
</para>
<xsl:template match="image" mode="conv70to71">
    <xsl:choose>
        <!-- nothing to do if already at 7.1 -->
        <xsl:when test="@schemaversion > 7.0">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="7.1">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv70to71"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv70to71">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv70to71"/>
    </xsl:copy>
</xsl:template>

<!-- delete type from repository if obsolete type spec is used -->
<xsl:template match="repository" mode="conv70to71">
    <xsl:choose>
        <xsl:when test="@type='red-carpet' or @type='slack-site' or @type='up2date-mirrors' or @type='urpmi' or @type='yast2'">
            <repository>
                <xsl:copy-of select="@*[not(local-name(.) = 'type')]"/>
                <xsl:apply-templates mode="conv70to71"/>
            </repository>
        </xsl:when>
        <xsl:otherwise>
            <xsl:copy-of select="."/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
