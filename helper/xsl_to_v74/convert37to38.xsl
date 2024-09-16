<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- default rule -->
<xsl:template match="*" mode="conv37to38">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv37to38"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>3.7</literal> to <literal>3.8</literal>.
</para>
<xsl:template match="image" mode="conv37to38">
    <xsl:choose>
        <!-- nothing to do if already at 3.8 -->
        <xsl:when test="@schemaversion > 3.7">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="3.8">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv37to38"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv37to38">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv37to38"/>
    </xsl:copy>
</xsl:template>

<!-- update deploy / pxedeploy -->
<para xmlns="http://docbook.org/ns/docbook"> 
    Change attribute value <tag class="attribute">deploy</tag> to 
    <tag class="attribute">pxedeploy</tag>.
</para>
<xsl:template match="deploy" mode="conv37to38">
    <pxedeploy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv37to38"/>
    </pxedeploy>
</xsl:template>

</xsl:stylesheet>
