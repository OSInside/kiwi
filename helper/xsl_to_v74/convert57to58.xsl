<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv57to58">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv57to58"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>5.7</literal> to <literal>5.8</literal>.
</para>
<xsl:template match="image" mode="conv57to58">
    <xsl:choose>
        <!-- nothing to do if already at 5.8 -->
        <xsl:when test="@schemaversion > 5.7">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="5.8">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv57to58"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv57to58">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv57to58"/>
    </xsl:copy>
</xsl:template>

<!-- remove syncMBR attribute from type -->
<para xmlns="http://docbook.org/ns/docbook">
    Remove obsolete syncMBR attribute from type
</para>
<xsl:template match="type" mode="conv57to58">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'syncMBR')]"/>
        <xsl:apply-templates mode="conv57to58"/>
    </type>
</xsl:template>

</xsl:stylesheet>
